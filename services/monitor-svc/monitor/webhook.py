import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta

import numpy as np
import requests
from labelbox import Label
from src.bounding_box import BBFormat, BoundingBox
from src.evaluators.coco_evaluator import get_coco_summary

from monitor.common import s3_client
from monitor.settings import PROJECT

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def list_annotations(date, bucket_name="annotations"):
    datetime.strptime(date, "%d-%m-%Y")
    return list(
        s3_client.list_objects(Bucket=bucket_name, Prefix=date).get("Contents", [])
    )


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def normalize_bbox(bbox):
    return [
        bbox["left"],
        bbox["top"],
        bbox["left"] + bbox["width"],
        bbox["top"] + bbox["height"],
    ]


def swap_dims(box, image_h, image_w):
    return [box[1] * image_w, box[0] * image_h, box[3] * image_w, box[2] * image_h]


def get_summary(preds, gts):
    result = get_coco_summary(gts, preds)
    result = {
        k: v
        for k, v in result.items()
        if k in ["AP", "AP50", "AP75", "AR1", "AR10", "AR100"] and not np.isnan(v)
    }
    scores = np.array([pred._confidence for pred in preds])
    result["mean_score"] = scores.mean()
    result["max_score"] = scores.max()
    result["min_score"] = scores.min()
    result["predictions"] = len(preds)
    result["labels"] = len(gts)

    return result


def construct_boxes(inference, annotation, name="exp_name"):
    annotation_boxes = [normalize_bbox(box) for box in annotation["boxes"]]
    image_size = (inference["image_w"], inference["image_h"])
    gt = [
        BoundingBox(
            name,
            class_id=class_name,
            coordinates=coords,
            format=BBFormat.XYX2Y2,
            img_size=image_size,
        )
        for coords, class_name in zip(annotation_boxes, annotation["class_names"])
    ]
    pred = [
        BoundingBox(
            name,
            class_id=class_name,
            coordinates=swap_dims(coords, image_size[1], image_size[0]),
            img_size=image_size,
            format=BBFormat.XYX2Y2,
            confidence=score,
        )
        for coords, score, class_name in zip(
            inference["boxes"], inference["scores"], inference["class_names"]
        )
    ]
    return gt, pred


def process_review_webhook(payload, lbclient, influx_client):
    """"""
    review = json.loads(payload.decode("utf8"))
    label = lbclient._get_single(Label, review["label"]["id"])
    data_row = label.data_row()
    # Process & store labels
    instances = json.loads(label.label)["objects"]
    boxes = [annot["bbox"] for annot in instances]
    class_names = [annot["title"] for annot in instances]
    annotation = {"boxes": boxes, "class_names": class_names}
    # push to s3
    s3_client.put_object(
        Body=str(json.dumps(annotation)),
        Bucket="annotations",
        Key=f"{data_row.external_id}.json",
    )
    # load corresponding inference
    inference = json.loads(
        s3_client.get_object(
            Bucket="results",
            Key=f"{data_row.external_id}.json")
        ["Body"].read()
    )

    # transform bounding boxes
    gt, pred = construct_boxes(inference=inference, annotation=annotation)
    summary = get_summary(pred, gt)

    # format InfluxDB
    json_body = [
        {
            "measurement": "model-stats",
            "tags": {
                "model_name": inference["model_name"],
                "model_version": inference["model_version"],
            },
            "time": inference["timestamp"],
            "fields": {
                **summary,
                **{
                    "review_score": review["score"],
                    "label_id": review["label"]["id"],
                    "external_id": data_row.external_id,
                    "datarow_link": f"https://app.labelbox.com/dataset/{data_row.dataset().uid}/{data_row.uid}",
                    "image_link": data_row.row_data,

                },
            },
        }
    ]
    influx_client.write_points(json_body)
    logger.info("success")
    return "success"


def init_ngrok():
    ng_auth_token = os.environ["NGROK_TOKEN"]
    subprocess.check_output(f"ngrok authtoken {ng_auth_token}".split(" "))
    os.system("ngrok http 5000 &")
    time.sleep(5)


def update_public_url():
    # We need to update the url in labelbox each time we start the server since it changes
    res = requests.get("http://localhost:4040/api/tunnels")
    assert (
            res.status_code == 200
    ), f"ngrok probably isn't running. {res.status_code}, {res.text}"
    tunnel = [t for t in res.json()["tunnels"] if t["config"]["addr"].split(":")[-1] == str(5000)]
    public_url = tunnel[0]["public_url"]
    logger.info(public_url)
    webhook = next(PROJECT.webhooks())
    webhook.update(url=public_url + "/review")
    return public_url
