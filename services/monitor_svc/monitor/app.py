import hashlib
import hmac

from flask import request, Flask
from influxdb import InfluxDBClient
from labelbox import Client


from resources.common import get_logger
from resources.settings import (
    INFLUXDB_HOST,
    INFLUXDB_PORT,
    INFLUXDB_USR,
    INFLUXDB_PAS,
    INFLUXDB_NAME
)
from resources.secrets import secret

from monitor_svc.monitor.webhook import (
    process_review_webhook,
    init_ngrok,
    update_public_url
)

client = Client()

app = Flask(__name__)
logger = get_logger(app, "metrics-logger")


def make_influx_db_client():
    db_client = InfluxDBClient(
        INFLUXDB_HOST, INFLUXDB_PORT, INFLUXDB_USR, INFLUXDB_PAS, INFLUXDB_NAME
    )
    db_client.create_database(INFLUXDB_NAME)
    return db_client


influx_client = make_influx_db_client()


@app.route("/")
def health_check():
    return "alive!"

@app.route("/review", methods=["POST"])
def process_webhook():
    raise Exception(".....")
    payload = request.data
    verify_webhook(payload)
    return process_review_webhook(payload, client, influx_client)


def verify_webhook(payload):
    computed_signature = hmac.new(
        secret,
        msg=payload,
        digestmod=hashlib.sha1
    ).hexdigest()
    if request.headers["X-Hub-Signature"] != "sha1=" + computed_signature:
        return "Error: computed_signature does not match signature provided in the headers", 500, 200


def main():
    init_ngrok()
    url = update_public_url()
    logger.info(url)
    logger.info("Started...")
    app.run(host="0.0.0.0", threaded=True, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
