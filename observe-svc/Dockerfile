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
                schedule \
                labelbox \
                boto3 \
                opencv-python \
                git+https://github.com/rafaelpadilla/review_object_detection_metrics.git \
                pip install json-logging \
                pyqt5


WORKDIR /usr/src/observe-svc/
COPY ./observe-svc .

CMD python service.py
#; python uploads.py
