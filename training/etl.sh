docker build -f Dockerfile . -t od
docker run -e LABELBOX_API_KEY=$LABELBOX_API_KEY -p 8078:8078 -v /tmp:/tmp -u 0 -it od /bin/bash -c "python etl.py"
