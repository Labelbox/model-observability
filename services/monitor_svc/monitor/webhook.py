import json
import logging
import os
import time
import subprocess
from uuid import uuid4
import time
from typing import Optional, Dict, Any

import requests
from influxdb import InfluxDBClient
from labelbox import Label, Client, DataRow
from labelbox.data.metrics.iou import datarow_miou

from resources.common import s3_client
from resources.settings import PROJECT, MODEL_RUN
from monitor_svc.monitor.processing import format_annotation, construct_boxes, get_summary

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def init_ngrok():
    """ Enables your local deployment to have a public ip address """
    ng_auth_token = os.environ["NGROK_TOKEN"]
    subprocess.check_output(f"ngrok authtoken {ng_auth_token}".split(" "))
    os.system("ngrok http 5000 &")
    time.sleep(5)


def update_public_url(webhook_host: Optional[str]) -> str:
    # We need to update the url in labelbox each time we start the server since it changes when using ngrok
    if not webhook_host:
        res = requests.get("http://localhost:4040/api/tunnels")
        assert (res.status_code == 200
               ), f"ngrok probably isn't running. {res.status_code}, {res.text}"
        tunnel = [
            t for t in res.json()["tunnels"]
            if t["config"]["addr"].split(":")[-1] == str(5000)
        ]
        webhook_host = tunnel[0]["public_url"]
    logger.info(webhook_host)
    webhook = next(PROJECT.webhooks())
    webhook.update(url=webhook_host + "/review")
    return webhook_host


def process_review_webhook(payload: Dict[str, Any], lbclient: Client,
                           influx_client: InfluxDBClient) -> str:
    """
    This is the logic that is triggered each time a webhook event occurs.
        - Parse the webhook results to use as the annotation
        - Fetch the original inference
        - Compute metrics
        - Write to influx db
        - Upload to MEA
    """
    logger.info("webhook recieved")
    review = json.loads(payload.decode("utf8"))
    label = lbclient._get_single(Label, review["label"]["id"])
    data_row = label.data_row()
    json_label = json.loads(label.label)
    # Process & store labels
    annotation = format_annotation(json_label)
    # load corresponding inference
    inference = fetch_inference(data_row)
    gt, pred = construct_boxes(inference=inference, annotation=annotation)
    summary = get_summary(pred, gt)

    write_to_influx(influx_client, inference, review, data_row, summary)
    write_to_mea(label, data_row, json_label, inference)
    return "success"


def fetch_inference(data_row: DataRow) -> Dict[str, Any]:
    """ Fetch model inference from s3 for a given data row """
    return json.loads(
        s3_client.get_object(Bucket="results",
                             Key=f"{data_row.external_id}.json")["Body"].read())


def write_to_mea(label: Label, data_row: DataRow, json_label: Dict[str, Any],
                 inference: Dict[str, Any]) -> None:
    """ Add the label and prediction to the model run """
    MODEL_RUN.upsert_labels([label.uid])
    time.sleep(
        1
    )  # Wait for upload to complete. This will be a task that we can wait on soon.
    metric = [
        datarow_miou({
            'DataRow ID': data_row.uid,
            'Label': json_label
        }, inference['ndjson_annotions'])
    ]
    MODEL_RUN.add_predictions(f'mea-import-{uuid4()}',
                              inference['ndjson_annotions'] + metric)


def write_to_influx(influx_client: InfluxDBClient, inference: Dict[str, Any],
                    review: Dict[str, Any], data_row: DataRow,
                    summary: Dict[str, Any]) -> None:
    """ Save the stats to influx db """
    json_body = [{
        "measurement": "model-stats",
        "tags": {
            "model_name": inference["model_name"],
            "model_version": inference["model_version"],
        },
        "time": inference["timestamp"],
        "fields": {
            **summary,
            **{
                "review_score":
                    review["score"],
                "label_id":
                    review["label"]["id"],
                "external_id":
                    data_row.external_id,
                "datarow_link":
                    f"https://app.labelbox.com/dataset/{data_row.dataset().uid}/{data_row.uid}",
                "image_link":
                    data_row.row_data,
            },
        },
    }]
    influx_client.write_points(json_body)
