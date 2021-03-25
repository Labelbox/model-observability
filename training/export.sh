python object_detection/exporter_main_v2.py \
	--input_type image_tensor 
        --pipeline_config_path pipeline_proto/pipeline.config \
        --trained_checkpoint_dir /outputs \
	--output_directory servable/
