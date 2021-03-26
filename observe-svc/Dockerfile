FROM python:3.8

RUN curl -s -O https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip \
    && unzip ngrok-stable-linux-amd64.zip \
    && mv ngrok /usr/local/bin/ \
    && rm -f ngrok-stable-linux-amd64.zip

RUN pip install tensorflow-serving-api \
                tensorflow \
                PILLOW \
                numpy \
                flask \
                schedule \
                labelbox \
                boto3 \
                git+https://github.com/rafaelpadilla/review_object_detection_metrics.git \
                pyqt5


WORKDIR /usr/src/observe-svc/
COPY ./observe-svc .

CMD python service.py
######CMD python service.py ; python ./uploads.py
