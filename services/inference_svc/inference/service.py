import json
import os
from datetime import datetime
from io import BytesIO
from uuid import uuid4

import random

import flask
from flask import request
from PIL import Image

from resources.settings import KEEP_PROB
from resources.common import get_logger, s3_client
from inference_svc.inference.tf_client import Predictor
from inference_svc.inference.upload import upload_annotations

predictor = Predictor()

app = flask.Flask(__name__)
logger = get_logger(app, "inference-logger")


@app.route("/")
def healh_check():
    return "Running"


@app.route("/predict", methods=["POST"])
def predict_sync():
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            image_bytes = flask.request.files['image'].read()

    # Fixed image size.
    image = Image.open(BytesIO(image_bytes)).resize((320, 320))
    boxes, scores, class_names = predictor.predict(image)

    response = {
        'boxes': boxes.tolist(),
        'scores': scores.tolist(),
        'class_names': class_names
    }
    if random.random() < KEEP_PROB:
        store_results(image, response.copy(), request.args.get('date'))
    logger.info({"objects_detected": len(boxes)})
    return response


def store_results(image, response, date_override=None):
    uuid = str(uuid4())
    timestamp = datetime.now()
    # Allow user to simulate different dates for testing
    # In prod we wouldn't override the date
    day = date_override if date_override else timestamp.strftime("%d-%m-%Y")

    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")

    s3_client.put_object(
        Body=image_bytes.getvalue(),
        Bucket='images',
        Key=os.path.join(day, f"{uuid}.jpg")
    )
    external_id = os.path.join(day, uuid)
    ndjson_annotions = upload_annotations(
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
            'model_name': 'animal-detector',
            'model_version': '0.0.1'
        }
    )
    s3_client.put_object(
        Body=str(json.dumps(response)),
        Bucket='results',
        Key=f"{external_id}.json"
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5100')
