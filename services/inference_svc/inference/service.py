from io import BytesIO
import random
import flask
from flask import request
from PIL import Image

from resources.settings import KEEP_PROB, IMAGE_H, IMAGE_W
from resources.common import get_logger
from inference_svc.inference.tf_client import Predictor
from inference_svc.inference.upload import store_results

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

    image = Image.open(BytesIO(image_bytes)).resize((IMAGE_W, IMAGE_H))
    boxes, scores, class_names = predictor.predict(image)

    response = {
        'boxes': boxes.tolist(),
        'scores': scores.tolist(),
        'class_names': class_names
    }
    if random.random() < KEEP_PROB:
        store_results(image, response.copy())
    logger.info({"objects_detected": len(boxes)})
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5100')
