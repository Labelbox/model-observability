FROM python:3.8

RUN pip install tensorflow-serving-api \
                tensorflow \
                labelbox \
                PILLOW \
                numpy \
                flask \
                boto3 \
                json_logging


WORKDIR /usr/src/
COPY . .
CMD python -m inference_svc.inference.service
