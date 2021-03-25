FROM python:3.8

RUN pip install tensorflow-serving-api \
                tensorflow \
                PILLOW \
                numpy \
                flask \
                boto3


WORKDIR /usr/src/animal-svc
COPY ./animal-svc .

CMD ["python", "./service.py"]
