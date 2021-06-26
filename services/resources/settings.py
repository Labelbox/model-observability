import json
import os

from labelbox import Client


conf_file = "resources/project_conf.json"
client = Client()

project_conf = json.load(open(conf_file, 'r'))

INFLUXDB_USR = os.environ.get("INFLUXDB_USR")
INFLUXDB_PAS = os.environ.get("INFLUXDB_PAS")
INFLUXDB_NAME = os.environ.get("INFLUXDB_NAME", "monitoring-db")
INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", "influxdb")
INFLUXDB_PORT = os.environ.get("INFLUXDB_PORT", 8086)

PROJECT = client.get_project(project_conf['project_id'])
DATASET = client.get_dataset(project_conf['dataset_id'])
BBOX_FEATURE_SCHEMA_ID = project_conf['bbox_feature_schema_id']
TEXT_FEATURE_SCHEMA_ID = project_conf['text_feature_schema_id']

# Save all for now
KEEP_PROB = 1.0

MODEL_CLASS_MAPPINGS = {
    16 : 'bird',
    17: 'cat',
    18: 'dog',
    19: 'horse',
    20: 'sheep',
    21: 'cow',
    22: 'elephant',
    23: 'bear',
    24: 'zebra',
    25: 'giraffe'
}
