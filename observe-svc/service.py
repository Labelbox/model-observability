from datetime import datetime, timedelta
import json
import hashlib
import subprocess
import requests
from uploads import PROJECT
from labelbox import Client
import time
import subprocess
import hmac
import random
from flask import Flask
from flask import request
import os
import boto3
from labelbox import Client, Label
import numpy as np
from src.evaluators.coco_evaluator import get_coco_summary
from src.bounding_box import BBFormat, BBType, CoordinatesType, BoundingBox
import logging
import sys, json_logging

logging.basicConfig()

client = Client()

app = Flask(__name__)
json_logging.init_flask(enable_json=True)
json_logging.init_request_instrument(app)

# init the logger as usual
logger = logging.getLogger("test-logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)



secret = b'webhook_secret'
default_access_key_id = "AKIAIOSFODNN7EXAMPLE"
default_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

session = boto3.session.Session()


s3_client = session.client(
    service_name='s3',
    aws_access_key_id=default_access_key_id,
    aws_secret_access_key=default_access_key,
    endpoint_url='http://storage:9000',
)

ng_auth_token = os.environ['NGROK_TOKEN']
subprocess.check_output(f"ngrok authtoken {ng_auth_token}".split(' '))
os.system('ngrok http 5000 &')
time.sleep(5)


def update_public_url():
    #We need to update the url in labelbox each time we start the server since it changes
    res = requests.get('http://localhost:4040/api/tunnels')
    assert res.status_code == 200, f"ngrok probably isn't running. {res.status_code}, {res.text}"
    tunnels = res.json()['tunnels']
    tunnel = [
        t for t in tunnels if t['config']['addr'].split(':')[-1] == str(5000)
    ]
    tunnel = tunnel[0]  #Should only be one..
    public_url = tunnel['public_url']
    webhook = next(PROJECT.webhooks())
    webhook.update(url=public_url + "/review")


@app.route('/')
def health_check():
    return 'alive!'


@app.route('/review', methods=['POST'])
def print_webhook_info():
    payload = request.data
    computed_signature = hmac.new(secret, msg=payload,
                                  digestmod=hashlib.sha1).hexdigest()
    if request.headers['X-Hub-Signature'] != 'sha1=' + computed_signature:
        print(
            'Error: computed_signature does not match signature provided in the headers'
        )
        return 'Error', 500, 200
    review = json.loads(payload.decode('utf8'))
    label = client._get_single(Label, review['label']['id'])
    data_row = label.data_row()
    boxes = [annot['bbox'] for annot in json.loads(label.label)['objects']]
    #boxes = [normalize_box(box) for box in boxes]
    s3_client.put_object(Body=str(json.dumps({'boxes': boxes})),
                         Bucket='annotations',
                         Key=f"{data_row.external_id}.json")


    inference = json.loads(
                 s3_client.get_object(Bucket='results', Key=f"{data_row.external_id}.json")['Body'].read())
    gt, pred = calculate_accuracy(inference = inference, annotation = {'boxes': boxes})
    summary = get_summary(pred, gt)
    summary.update({'date' : data_row.external_id.split('/')[0]})
    summary.update({'external_id' : data_row.external_id})
    logger.info(summary)
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


def calculate_batch_accuracy(annotations, inferences):
    annotations = set([annot['Key'] for annot in annotations])
    inferences = set([infer['Key'] for infer in inferences])
    #Files should have the same name
    #Each example is an image
    gts, preds = [], []
    for example in annotations.intersection(inferences):
        annotation = json.loads(
                s3_client.get_object(Bucket='annotations',
                                 Key=example)['Body'].read())
        inference = json.loads(
                s3_client.get_object(Bucket='results', Key=example)['Body'].read())
        gt, pred = calculate_accuracy(inference, annotation, name = example)
        gts.extend(gt)
        preds.extend(pred)

    if not len(gt):
        return {'samples': 0}

    result = get_summary(preds, gts)
    return result


def get_summary(preds, gts):
    result = get_coco_summary(gts, preds)
    result = {
        k: v for k, v in result.items() if
        k in ['AP', 'AP50', 'AP75', 'AR1', 'AR10', 'AR100'] and not np.isnan(v)
    }
    return result



def calculate_accuracy(inference, annotation, name = "placeholder"):
    annotation_boxes = [normalize_box(box) for box in annotation['boxes']]
    image_size = (inference['image_w'], inference['image_h'])
    gt = [BoundingBox(name, #always the same since we are doing one at a time
                        class_id="animal",
                        coordinates=coords,
                        format=BBFormat.XYX2Y2,
                        img_size=image_size) for coords in annotation_boxes
    ]
    pred = [BoundingBox(name,
                        class_id="animal",
                        coordinates=swap_dims(coords, image_size[1],
                                              image_size[0]),
                        img_size=image_size,
                        format=BBFormat.XYX2Y2,
                        confidence=score)
        for coords, score in zip(inference['boxes'], inference['scores'])
    ]
    return gt, pred

@app.route('/observe')
def observe():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date', start_date)
    #request_args.get('visualize', False)
    """
    This route will be used to see how the model is performing
    - Optionally visualize some failure to see the cause
    """
    ious = {}
    start_date = datetime.strptime(start_date, '%d-%m-%Y')
    end_date = datetime.strptime(end_date, '%d-%m-%Y')
    for date in daterange(start_date, end_date):
        date = date.strftime('%d-%m-%Y')
        annotations = list_annotations(date)
        inferences = list_annotations(date, bucket_name='results')
        ious[date] = calculate_accuracy(annotations, inferences)
    logger.info(ious)
    return ious



if __name__ == '__main__':
    update_public_url()
    print("Started...")
    app.run(host='0.0.0.0', threaded=True, debug=True, use_reloader = False)
