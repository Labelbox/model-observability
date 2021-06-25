FROM tensorflow/tensorflow:2.2.0-gpu

ARG DEBIAN_FRONTEND=noninteractive

# Install apt dependencies
RUN apt-get update && apt-get install -y \
    git \
    gpg-agent \
    python3-cairocffi \
    protobuf-compiler \
    python3-pil \
    python3-lxml \
    python3-tk \
    wget

# Install gcloud and gsutil commands
# https://cloud.google.com/sdk/docs/quickstart-debian-ubuntu
RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get update -y && apt-get install google-cloud-sdk -y

# Add new user to avoid running as root
WORKDIR /home/tensorflow

# Copy this version of of the model garden into the image
#COPY --chown=tensorflow . /home/tensorflow/models
RUN git clone https://github.com/tensorflow/models.git

# Compile protobuf configs
RUN (cd /home/tensorflow/models/research/ && protoc object_detection/protos/*.proto --python_out=.)
WORKDIR /home/tensorflow/models/research/

RUN cp object_detection/packages/tf2/setup.py ./
ENV PATH="/home/tensorflow/.local/bin:${PATH}"


RUN wget http://download.tensorflow.org/models/object_detection/tf2/20200711/ssd_resnet50_v1_fpn_640x640_coco17_tpu-8.tar.gz && \
        tar -xf ssd_resnet50_v1_fpn_640x640_coco17_tpu-8.tar.gz && \
        mv ssd_resnet50_v1_fpn_640x640_coco17_tpu-8/checkpoint object_detection/test_data/



RUN python -m pip install -U pip
RUN cp object_detection/packages/tf2/setup.py .
RUN pip install -U .
RUN pip install -U labelbox tqdm
RUN python -c "from object_detection.builders import model_builder"
RUN apt-get install -y vim 
COPY . .

ENV TF_CPP_MIN_LOG_LEVEL 3

