from labelbox import Client
import json
import boto3
import os
import logging
import json_logging
import sys

secret = b'webhook_secret'
conf_file = "project_conf.json"

if os.path.exists(conf_file):
    client = Client()
    project_conf = json.load(open(conf_file, 'r'))
    PROJECT = client.get_project(project_conf['project_id'])
    DATASET = client.get_dataset(project_conf['dataset_id'])
    BBOX_FEATURE_SCHEMA_ID = project_conf['bbox_feature_schema_id']
    TEXT_FEATURE_SCHEMA_ID = project_conf['text_feature_schema_id']

default_access_key_id = "AKIAIOSFODNN7EXAMPLE"
default_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

session = boto3.session.Session()
s3_client = session.client(
    service_name='s3',
    aws_access_key_id=default_access_key_id,
    aws_secret_access_key=default_access_key,
    endpoint_url='http://storage:9000',
)


def get_logger(app, name):
    logging.basicConfig()
    json_logging.init_flask(enable_json=True)
    json_logging.init_request_instrument(app)
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.INFO)
    return logger
