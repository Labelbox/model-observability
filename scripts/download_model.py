import tensorflow_hub as hub
import hashlib
import os

cache_dir = "/tmp/servable/saved_model"
model_url = "https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2"


os.environ['TFHUB_CACHE_DIR']= cache_dir


detector = hub.load(model_url)
model_path = os.path.join(cache_dir, hashlib.sha1(model_url.encode("utf8")).hexdigest())
model_versions = [int(version) for version in os.listdir(cache_dir) if version.isnumeric()] + [0]

if os.path.exists(model_path):
    os.rename(model_path, os.path.join(cache_dir, str(max(model_versions) + 1)))

