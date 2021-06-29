
import json
from resources.common import CLIENT

conf_file = "resources/labelbox_conf.json"
labelbox_conf = json.load(open(conf_file, 'r'))

PROJECT = CLIENT.get_project(labelbox_conf['project_id'])
DATASET = CLIENT.get_dataset(labelbox_conf['dataset_id'])
MODEL = CLIENT.get_model(labelbox_conf['model_id'])
# There should only be one model
MODEL_RUN = next(MODEL.model_runs())
BBOX_FEATURE_SCHEMA_ID = labelbox_conf['bbox_feature_schema_id']

# Set the host if you are running this on a server with a public ip address.
# Otherwise the app will use ngrok
WEBHOOK_HOST = None
