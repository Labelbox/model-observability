FROM python:3.8

RUN curl -s -O https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip \
    && unzip ngrok-stable-linux-amd64.zip \
    && mv ngrok /usr/local/bin/ \
    && rm -f ngrok-stable-linux-amd64.zip

RUN apt-get update && apt-get install -y python3-opencv
RUN pip install tensorflow-serving-api \
                tensorflow \
                PILLOW \
                numpy \
                matplotlib \
                flask \
                labelbox==2.7b1 \
                boto3 \
                opencv-python \
                json-logging \
                pyqt5 \
                influxdb \
                git+https://github.com/rafaelpadilla/review_object_detection_metrics.git

WORKDIR /usr/src/
COPY . .
CMD python -m monitor_svc.monitor.app
