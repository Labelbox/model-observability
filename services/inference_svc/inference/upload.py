from io import BytesIO
from datetime import datetime
import json
import os
import numpy as np
from typing import Dict, Any
from uuid import uuid4

from resources.common import s3_client
from resources.settings import MODEL_NAME, MODEL_VERSION
from inference_svc.inference.mal import mal_upload


def save_image_to_s3(image_bytes : BytesIO, external_id : str) -> None:
    """
    Saves and image on s3
    """
    s3_client.put_object(
        Body=image_bytes.getvalue(),
        Bucket='images',
        Key=f"{external_id}.jpg"
    )

def save_inference_to_s3(response : Dict[str, Any], external_id: str) -> None:
    """
    Saves a dictionary as json on s3
    """
    s3_client.put_object(
        Body=str(json.dumps(response)),
        Bucket='results',
        Key=f"{external_id}.json"
    )

def np_to_jpg_bytes(image: np.ndarray) -> BytesIO:
    """
    Converts a numpy array representation of an image to jpg encoded image bytes
    """
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")
    return image_bytes

def store_results(image: np.ndarray, response: Dict[str, Any]) -> None:
    """
    Saves an image and prediction pair to s3.
    Adds additional information to the inference useful for metrics collection.
    Uploads the inference to labelbox.
    """
    timestamp = datetime.now().strftime("%d-%m-%Y")
    external_id = os.path.join(timestamp, str(uuid4()))
    image_bytes = np_to_jpg_bytes(image)
    ndjson_annotions = mal_upload(
        image_bytes.getvalue(),
        external_id,
        response['boxes'],
        response['scores'],
        image.size[1],
        image.size[0]
    )
    response.update(
        {
            'timestamp': str(timestamp),
            'image_h': image.size[1],
            'image_w': image.size[0],
            'ndjson_annotions' : ndjson_annotions,
            'model_name': MODEL_NAME,
            'model_version': MODEL_VERSION
        }
    )
    save_inference_to_s3(response, external_id)
    save_image_to_s3(image_bytes, external_id)
