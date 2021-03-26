from datetime import datetime
import json
import hashlib
import subprocess
import requests
from uploads import PROJECT
from labelbox import Client
import time
import subprocess
import hmac
import random
from flask import Flask
from flask import request
import os
import boto3
from labelbox import Client, Label

client = Client()

app = Flask(__name__)

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

ng_auth_token = os.environ['NGROK_TOKEN']
subprocess.check_output(f"ngrok authtoken {ng_auth_token}".split(' '))
os.system('ngrok http 5000 &')
time.sleep(5)


def update_public_url():
    #We need to update the url in labelbox each time we start the server since it changes
    res = requests.get('http://localhost:4040/api/tunnels')
    assert res.status_code == 200, f"ngrok probably isn't running. {res.status_code}, {res.text}"
    tunnels = res.json()['tunnels']
    tunnel = [
        t for t in tunnels if t['config']['addr'].split(':')[-1] == str(5000)
    ]
    tunnel = tunnel[0]  #Should only be one..
    public_url = tunnel['public_url']
    webhook = next(PROJECT.webhooks())
    webhook.update(url=public_url + "/review")


@app.route('/')
def health_check():
    return 'alive!'


def normalize_box(box, image_h, image_w):
    box[0] = box[0] / image_h
    box[1] = box[1] / image_w
    box[2] = box[2] / image_h
    box[3] = box[3] / image_w
    return box



@app.route('/review', methods=['POST'])
def print_webhook_info():
    payload = request.data
    computed_signature = hmac.new(secret, msg=payload,
                                  digestmod=hashlib.sha1).hexdigest()
    if request.headers['X-Hub-Signature'] != 'sha1=' + computed_signature:
        print(
            'Error: computed_signature does not match signature provided in the headers'
        )
        return 'Error', 500, 200
    review = json.loads(payload.decode('utf8'))
    {'top': 290, 'left': 251, 'height': 107, 'width': 65}

                 t = bbox[0] * inference['image_h']
             l = bbox[1] * inference['image_w']
             b = bbox[2] * inference['image_h']
             r = bbox[3] * inference['image_w']


    label = client._get_single(Label, review['label']['id'])
    data_row = label.data_row()
    boxes = [annot['bbox'] for annot in json.loads(label.label)['objects']]
    boxes = []
    s3_client.put_object(Body=str(json.dumps({'boxes': boxes})),
                         Bucket='annotations',
                         Key=f"{data_row.external_id}.json")
    return "success"



def list_annotations(date, bucket_name="annotations"):
    datetime.strptime(date, '%d-%m-%Y')
    return list(
        s3_client.list_objects(Bucket=bucket_name, Prefix=date)['Contents'])

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

#https://github.com/rafaelpadilla/Object-Detection-Metrics/blob/master/samples/sample_2/sample_2.py
#Maybe use threading for this..
         image_res = s3_client.get_object(Bucket='images',
                                          Key=sample.replace('.json', '.jpg'))
         image_bytes = image_res['Body'].read()
         json_res = s3_client.get_object(Bucket='results', Key=sample)
         json_payload = json.loads(json_res['Body'].read().decode('utf-8'))

def get_bbox(response):





def calculate_accuracy(annotations, inferences):
    examples = set(annotations + inferences)
    #Files should have the same name
    #Each example is an image
    for example in examples:
        example = example['Key']
        annotation = s3_client.get_object(Bucket='annotations', Key = example)
        inference = s3_client.get_object(Bucket='inferences', Key = example)

        annotation =BoundingBox(example, coordinates = [annotation[]])

@app.route('/observe')
def observe():
    start_date = request_args.get('start_date')
    end_date = request_args.get('end_date', start_date)
    #request_args.get('visualize', False)
    """
    This route will be used to see how the model is performing
    - Optionally visualize some failure to see the cause
    """
    ious = {}
    for date in daterange(start_date, end_date):
        date = date.strftime('%d-%m-%Y')
        annotations = list_annotations(date)
        inferences = list_annotations(date, bucket_name = 'inferences')






if __name__ == '__main__':
    update_public_url()
    print("Started...")
    app.run(host='0.0.0.0', threaded=True)
