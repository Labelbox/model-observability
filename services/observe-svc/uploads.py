from labelbox.schema.ontology import OntologyBuilder, Tool, Classification, Option
from labelbox import Project, Dataset, Client, LabelingFrontend, Client
from datetime import datetime
import logging
import random
import json
import uuid
import time
from shared import s3_client, PROJECT, DATASET, BBOX_FEATURE_SCHEMA_ID, TEXT_FEATURE_SCHEMA_ID

client = Client()

logger = logging.getLogger("upload")


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

    logger.info("Starting upload..")
    upload_task = PROJECT.upload_annotations(name=f"upload-job-{uuid.uuid4()}",
                                             annotations=ndjsons,
                                             validate=False)


def upload_image_to_labelbox(image_bytes, external_id):
    uri = DATASET.client.upload_data(content=image_bytes, filename=external_id)
    data_row = DATASET.create_data_row(row_data=uri, external_id=external_id)
    return data_row


def list_inferences(date, bucket_name="results"):
    assert bucket_name in ['images', 'results'], bucket_name
    return list(
        s3_client.list_objects(Bucket=bucket_name, Prefix=date)['Contents'])


def sample_live_data():
    date = datetime.now().strftime('%d-%m-%Y')
    sample_training_data(date, target_examples = 25)


def sample_training_data(date, target_examples = 25):
    labels = list_inferences(date, 'results')
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
    if not len(to_upload):
        logger.info(f"No examples to upload for date {date}")
        return 0
    logger.info(f"Uploading {len(to_upload)} examples for date {date}")
    upload_annotations(to_upload)
    return len(to_upload)

def sample_every_n_hours(n = 3):
    while True:
        time.sleep(3600 * n)        
        sample_training_data()


if __name__ == '__main__':    
    sample_live_data()

