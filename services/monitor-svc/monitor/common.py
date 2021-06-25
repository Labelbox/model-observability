import boto3
import os
import logging
import json_logging
import sys

from monitor.settings import conf_file, DEFAULT_ACCESS_KEY_ID, DEFAULT_ACCESS_KEY

if os.path.exists(conf_file):
    pass

session = boto3.session.Session()
s3_client = session.client(
    service_name='s3',
    aws_access_key_id=DEFAULT_ACCESS_KEY_ID,
    aws_secret_access_key=DEFAULT_ACCESS_KEY,
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
