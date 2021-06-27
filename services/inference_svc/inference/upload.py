
import logging
from uuid import uuid4

from resources.settings import (
    PROJECT,
    DATASET,
    BBOX_FEATURE_SCHEMA_ID,
    TEXT_FEATURE_SCHEMA_ID,
    client
)

logger = logging.getLogger("upload")

def upload_annotations(image_bytes, external_id, boxes, scores, image_h, image_w):
    ndjsons = []
    data_row = _upload_image_to_labelbox(image_bytes, external_id)
    for bbox, score in zip(boxes, scores):
        top = bbox[0] * image_h
        left = bbox[1] * image_w
        bottom = bbox[2] * image_h
        right = bbox[3] * image_w
        ndjsons.append(
            _create_mal_bbox(data_row.uid, top, left, bottom, right, round(score, 2))
        )

    if ndjsons:
        PROJECT.upload_annotations(
            name=f"upload-job-{uuid4()}", annotations=ndjsons, validate=False
        )

def _upload_image_to_labelbox(image_bytes, external_id):
    uri = client.upload_data(content=image_bytes, filename=external_id)
    data_row = DATASET.create_data_row(row_data=uri, external_id=external_id)
    return data_row

def _create_mal_bbox(datarow_id, top, left, bottom, right, confidence):
    return {
        "uuid": str(uuid4()),
        "schemaId": BBOX_FEATURE_SCHEMA_ID,
        "dataRow": {"id": datarow_id},
        "bbox": {
            "top": int(top),
            "left": int(left),
            "height": int(bottom - top),
            "width": int(right - left),
        },
        "classifications": [
            {"schemaId": TEXT_FEATURE_SCHEMA_ID, "answer": str(confidence)}
        ],
    }
