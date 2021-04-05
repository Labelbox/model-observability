FROM python:3.8

RUN pip install tensorflow-serving-api \
                tensorflow \
                labelbox \
                PILLOW \
                numpy \
                flask \
                boto3 \
                json_logging


WORKDIR /usr/src/animal-svc
COPY ./animal-svc .
COPY shared.py .
CMD ["python", "./service.py"]
