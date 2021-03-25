FROM python:3.8

RUN pip install tensorflow-serving-api \
                tensorflow \
                PILLOW \
                numpy \
                flask


WORKDIR /usr/src/observe-svc/
COPY ./observe-svc .

CMD ["python", "-c" , "print(1)"]
