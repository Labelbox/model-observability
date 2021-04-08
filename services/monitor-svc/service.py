import hashlib
import hmac
import json
import os
import subprocess
import time
from datetime import datetime, timedelta

import numpy as np
import requests
from flask import Flask
from flask import request
from influxdb import InfluxDBClient
from labelbox import Client, Label
from src.bounding_box import BBFormat, BoundingBox
from src.evaluators.coco_evaluator import get_coco_summary

from settings import INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USR, INFLUXDB_PAS, INFLUXDB_NAME
from shared import secret, get_logger, s3_client, PROJECT
from uploads import sample_training_data

client = Client()

app = Flask(__name__)
logger = get_logger(app, "metrics-logger")


def make_influx_db_client():
    db_client = InfluxDBClient(
        INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USR, INFLUXDB_PAS, INFLUXDB_NAME
    )
    db_client.create_database(INFLUXDB_NAME)
    return db_client


influx_client = make_influx_db_client()


def init_ngrok():
    ng_auth_token = os.environ['NGROK_TOKEN']
    subprocess.check_output(f"ngrok authtoken {ng_auth_token}".split(' '))
    os.system('ngrok http 5000 &')
    time.sleep(5)


def update_public_url():
    # We need to update the url in labelbox each time we start the server since it changes
    res = requests.get('http://localhost:4040/api/tunnels')
    assert res.status_code == 200, f"ngrok probably isn't running. {res.status_code}, {res.text}"
    tunnels = res.json()['tunnels']
    tunnel = [
        t for t in tunnels if t['config']['addr'].split(':')[-1] == str(5000)
    ]
    tunnel = tunnel[0]  # Should only be one..
    public_url = tunnel['public_url']
    webhook = next(PROJECT.webhooks())
    webhook.update(url=public_url + "/review")


@app.route('/')
def health_check():
    return 'alive!'


@app.route('/force-sample', methods=['POST'])
def force_upload():
    date = request.args.get("date")
    return f"N samples {sample_training_data(date)} for date {date}"


@app.route('/review', methods=['POST'])
def print_webhook_info():
    payload = request.data
    computed_signature = hmac.new(
        secret,
        msg=payload,
        digestmod=hashlib.sha1
    ).hexdigest()
    if request.headers['X-Hub-Signature'] != 'sha1=' + computed_signature:
        print(
            'Error: computed_signature does not match signature provided in the headers'
        )
        return 'Error', 500, 200

    review = json.loads(payload.decode('utf8'))
    label = client._get_single(Label, review['label']['id'])
    data_row = label.data_row()

    # Project must only have bounding box tools.
    boxes = [annot['bbox'] for annot in json.loads(label.label)['objects']]
    class_names = [
        annot['title'] for annot in json.loads(label.label)['objects']
    ]
    annotation = {'boxes': boxes, 'class_names': class_names}
    s3_client.put_object(
        Body=str(json.dumps(annotation)),
        Bucket='annotations',
        Key=f"{data_row.external_id}.json"
    )

    inference = json.loads(
        s3_client.get_object(
            Bucket='results',
            Key=f"{data_row.external_id}.json")['Body'].read()
    )

    gt, pred = construct_boxes(inference=inference, annotation=annotation)
    summary = get_summary(pred, gt)

    parsed_ts = (
        datetime
            .strptime(data_row.external_id.split('/')[0], '%d-%m-%Y')
            .strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    )

    json_body = [
        {
            "measurement": "model-stats",
            "tags": {
                "model_name": inference["model_name"],
                "model_version": inference["model_version"]
            },
            "time": parsed_ts,
            "fields": {
                **summary

            },
        }
    ]
    influx_client.write_points(json_body)

    for k, v in summary.items():
        logger.info(
            {
                'class_name': k,
                'external_id': data_row.external_id,
                'date': parsed_ts,
                'metrics': v,
            }
        )
    return "success"


def list_annotations(date, bucket_name="annotations"):
    datetime.strptime(date, '%d-%m-%Y')
    return list(
        s3_client.list_objects(Bucket=bucket_name,
                               Prefix=date).get('Contents', []))


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def normalize_box(box):
    return [
        box['left'], box['top'], box['left'] + box['width'],
                                 box['top'] + box['height']
    ]


def swap_dims(box, image_h, image_w):
    return [
        box[1] * image_w, box[0] * image_h, box[3] * image_w, box[2] * image_h
    ]


def get_summary(preds, gts):
    result = get_coco_summary(gts, preds)
    result = {
        k: v
        for k, v in result.items()
        if k in ['AP', 'AP50', 'AP75', 'AR1', 'AR10', 'AR100'] and
           not np.isnan(v)
    }
    scores = np.array([pred._confidence for pred in preds])
    result['mean_score'] = scores.mean()
    result['max_score'] = scores.max()
    result["min_score"] = scores.min()
    result['predictions'] = len(preds)
    result['labels'] = len(gts)

    return result


def construct_boxes(inference, annotation, name="exp_name"):
    annotation_boxes = [normalize_box(box) for box in annotation['boxes']]
    image_size = (inference['image_w'], inference['image_h'])
    gt = [
        BoundingBox(
            name,
            class_id=class_name,
            coordinates=coords,
            format=BBFormat.XYX2Y2,
            img_size=image_size) for coords, class_name in zip(
            annotation_boxes, annotation['class_names'])
    ]
    pred = [
        BoundingBox(
            name,
            class_id=class_name,
            coordinates=swap_dims(coords, image_size[1], image_size[0]),
            img_size=image_size,
            format=BBFormat.XYX2Y2,
            confidence=score
        ) for coords, score, class_name in
        zip(inference['boxes'], inference['scores'], inference['class_names'])
    ]
    return gt, pred


if __name__ == '__main__':
    init_ngrok()
    update_public_url()
    print("Started...")
    app.run(host='0.0.0.0', threaded=True, debug=True, use_reloader=False)
