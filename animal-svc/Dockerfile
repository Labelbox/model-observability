FROM python:3.8

RUN pip install tensorflow-serving-api \
                tensorflow \
                PILLOW \
                numpy \
                flask \
                boto3 \
                json_logging


WORKDIR /usr/src/animal-svc
COPY ./animal-svc .

CMD ["python", "./service.py"]
