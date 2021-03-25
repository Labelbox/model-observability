import flask
import os
from PIL import Image
import numpy as np
from tf_client import Predictor
from io import BytesIO
from flask import jsonify
from datetime import datetime
from uuid import uuid4
import json



predictor = Predictor()


app = flask.Flask(__name__)


@app.route("/")
def healh_check():
    return "Running"



@app.route("/predict", methods=["POST"])
def predict_sync():
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            image_bytes = flask.request.files['image'].read()

    image = Image.open(BytesIO(image_bytes)).resize((640,640))
    boxes, scores = predictor.predict(image)

    response = {'boxes' : boxes.tolist(), 'scores' : scores.tolist()}
    store_results(image, response.copy())
    return response
    
def store_results(image, response):
    #Write to a persistent store. Using local files until I get cloud storage access
    uuid = str(uuid4())

    timestamp = datetime.now()
    day = timestamp.strftime("%d-%m-%Y")
    image_dir = os.path.join('results', 'images', day)
    response_dir = os.path.join('results', 'responses', day)
    
    for dir_name in [image_dir, response_dir]:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

    image.save(os.path.join(image_dir, f"{uuid}.jpg"))
    response.update({'timestamp' : str(timestamp)}) 

    with open(os.path.join(response_dir, f"{uuid}.json"), "w") as f:
        json.dump(response, f)

    


if __name__ == '__main__':
    app.run(host = '0.0.0.0')
