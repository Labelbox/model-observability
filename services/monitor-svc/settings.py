import os

INFLUXDB_USR = os.environ.get("INFLUXDB_USR")
INFLUXDB_PAS = os.environ.get("INFLUXDB_PAS")
INFLUXDB_NAME = os.environ.get("INFLUXDB_NAME", "monitoring-db")
INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", "http:")
INFLUXDB_PORT = os.environ.get("INFLUXDB_PORT", 8086)