
import os

INFLUXDB_USR = os.environ.get("INFLUXDB_USR")
INFLUXDB_PAS = os.environ.get("INFLUXDB_PAS")
INFLUXDB_NAME = os.environ.get("INFLUXDB_NAME", "monitoring-db")
INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", "influxdb")
INFLUXDB_PORT = os.environ.get("INFLUXDB_PORT", 8086)

# Save all for now
KEEP_PROB = 1.0

MODEL_CLASS_MAPPINGS = {9: 'boat'}

MODEL_NAME = "boat-detector"
MODEL_VERSION = "0.0.1"
IMAGE_H = 320
IMAGE_W = 320
