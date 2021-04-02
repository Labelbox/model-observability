from labelbox.schema.ontology import OntologyBuilder, Tool, Classification, Option
from labelbox import Project, Dataset, Client, LabelingFrontend, Client
from datetime import datetime
import logging
import schedule
import random
import json
import boto3
import uuid
import time

client = Client()

project_conf = json.load(open('project_conf.json', 'r'))
PROJECT = client.get_project(project_conf['project_id'])
DATASET = client.get_dataset(project_conf['dataset_id'])
BBOX_FEATURE_SCHEMA_ID = project_conf['bbox_feature_schema_id']
TEXT_FEATURE_SCHEMA_ID = project_conf['text_feature_schema_id']

logger = logging.getLogger("uploads")

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


def create_boxes_ndjson(datarow_id, t, l, b, r, confidence):
    return {
        "uuid":
            str(uuid.uuid4()),
        "schemaId":
            BBOX_FEATURE_SCHEMA_ID,
        "dataRow": {
            "id": datarow_id
        },
        "bbox": {
            "top": int(t),
            "left": int(l),
            "height": int(b - t),
            "width": int(r - l)
        },
        "classifications": [{
            'schemaId': TEXT_FEATURE_SCHEMA_ID,
            'answer': str(confidence)
        }]
    }


def upload_annotations(examples):
    #Error handling needs to be supported.. eg. write out error file url.
    ndjsons = []
    for example in examples:
        inference = example[1]
        for bbox, confidence in zip(inference['boxes'], inference['scores']):
            t = bbox[0] * inference['image_h']
            l = bbox[1] * inference['image_w']
            b = bbox[2] * inference['image_h']
            r = bbox[3] * inference['image_w']
            ndjsons.append(
                create_boxes_ndjson(example[0].uid, t, l, b, r,
                                    round(confidence, 2)))

    print("Starting upload..", flush=True)
    upload_task = PROJECT.upload_annotations(name=f"upload-job-{uuid.uuid4()}",
                                             annotations=ndjsons,
                                             validate=False)
    upload_task.wait_until_done()
    print("Upload complete..", flush=True)


def upload_image_to_labelbox(image_bytes, external_id):
    uri = DATASET.client.upload_data(content=image_bytes, filename=external_id)
    data_row = DATASET.create_data_row(row_data=uri, external_id=external_id)
    return data_row


def list_inferences(date, bucket_name="results"):
    assert bucket_name in ['images', 'results'], bucket_name
    return list(
        s3_client.list_objects(Bucket=bucket_name, Prefix=date)['Contents'])


def sample_training_data(low_confidence=False, target_examples=25):
    #TODO: Should support a demo mode where it just uploads everything..
    
    date = datetime.now().strftime('%d-%m-%Y')
    #TODO: Check if external ids have already been uploaded
    labels = list_inferences(date, 'results')
    print("LABELS", labels, flush=True)
    external_ids = [data_row.external_id for data_row  in DATASET.data_rows()]
    labels = [l for l in labels if l['Key'].replace('.json', '') not in external_ids]
    samples = random.sample(labels, min(len(labels), target_examples))
    to_upload = []

    for sample in samples:
        sample = sample['Key']
        image_res = s3_client.get_object(Bucket='images',
                                         Key=sample.replace('.json', '.jpg'))
        image_bytes = image_res['Body'].read()
        json_res = s3_client.get_object(Bucket='results', Key=sample)
        json_payload = json.loads(json_res['Body'].read().decode('utf-8'))
        external_id = sample.replace('.json', '')

        # Don't upload if we already uploaded a file on a given day.
        if external_id in external_ids:
            continue
        data_row = upload_image_to_labelbox(image_bytes, external_id)
        to_upload.append([data_row, json_payload, external_id])
    upload_annotations(to_upload)

#print(__name__, flush = True)
#if __name__ == '__main__' or __name__ == 'uploads':
#    sample_training_data()
#    schedule.every(10).minutes.do(lambda: sample_training_data)
#    while 1:
#        schedule.run_pending()
