import tensorflow_hub as hub
import hashlib
import os

# Where to save the model locally ( this needs to match the tf-server config in the docker-compose file )
cache_dir = "/tmp/servable/saved_model"
# The tensorflow hub model to use ( select from here https://tfhub.dev/s?module-type=image-object-detection )
model_url = "https://tfhub.dev/tensorflow/ssd_mobilenet_v2/2"

os.environ['TFHUB_CACHE_DIR'] = cache_dir

# Download
detector = hub.load(model_url)

# The rest of the code renames the downloaded model so that tf serving knows that this is the latest model
model_path = os.path.join(cache_dir,
                          hashlib.sha1(model_url.encode("utf8")).hexdigest())
model_versions = [
    int(version) for version in os.listdir(cache_dir) if version.isnumeric()
] + [0]


if os.path.exists(model_path):
    os.rename(model_path, os.path.join(cache_dir, str(max(model_versions) + 1)))
