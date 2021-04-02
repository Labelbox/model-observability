import flask
from flask import request
import os
from PIL import Image
import numpy as np
from tf_client import Predictor
from io import BytesIO
from flask import jsonify
from datetime import datetime
from uuid import uuid4
import json
import boto3

predictor = Predictor()

app = flask.Flask(__name__)

#These only work locally..
default_access_key_id = "AKIAIOSFODNN7EXAMPLE"
default_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

session = boto3.session.Session()
s3_client = session.client(
    service_name='s3',
    aws_access_key_id=default_access_key_id,
    aws_secret_access_key=default_access_key,
    endpoint_url='http://storage:9000',
)

@app.route("/")
def healh_check():
    return "Running"

@app.route("/predict", methods=["POST"])
def predict_sync():
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            image_bytes = flask.request.files['image'].read()

    image = Image.open(BytesIO(image_bytes)).resize((640, 640))
    boxes, scores = predictor.predict(image)

    response = {'boxes': boxes.tolist(), 'scores': scores.tolist()}
    store_results(image, response.copy(), request.args.get('date'))

    return response


def store_results(image, response, date_override = None):
    uuid = str(uuid4())
    timestamp = datetime.now()
    # Allow user to simulate different dates for testing
    # In prod we wouldn't override the date
    if date_override is None:
        day = timestamp.strftime("%d-%m-%Y")
    else:
        day = date_override

    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")
    s3_client.put_object(Body=image_bytes.getvalue(),
                         Bucket='images',
                         Key=os.path.join(day, f"{uuid}.jpg"))

    response.update({
        'timestamp': str(timestamp),
        'image_h': image.size[1],
        'image_w': image.size[0]
    })

    s3_client.put_object(Body=str(json.dumps(response)),
                         Bucket='results',
                         Key=os.path.join(day, f"{uuid}.json"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')
