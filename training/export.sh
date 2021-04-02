
docker build -f Dockerfile . -t od
 docker run -e LABELBOX_API_KEY=$LABELBOX_API_KEY -p 8078:8078 -v /tmp:/tmp -u 0 -it od /bin/bash -c "python update_protos.py && python object_detection/exporter_main_v2.py \
	--input_type image_tensor \
        --pipeline_config_path pipeline_proto/pipeline.config \
        --trained_checkpoint_dir /tmp/outputs \
	--output_directory /tmp/servable/ && mkdir /tmp/servable/saved_model/1 && mv /tmp/servable/saved_model/* /tmp/servable/saved_model/1/"
