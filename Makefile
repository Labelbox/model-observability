MODEL_CMD = docker run -e LABELBOX_API_KEY=${LABELBOX_API_KEY} -p 8078:8078 -v /tmp:/tmp -u 0 -it animal_training /bin/bash -c

build-train:
	docker build -f training/Dockerfile training/ -t animal_training

etl: build-train
	@$(MODEL_CMD) "python etl.py"

train: build-train
	@$(MODEL_CMD) "python train.py"
	
export: build-train
	@$(MODEL_CMD) \
		"python update_protos.py && \
	     python object_detection/exporter_main_v2.py \
            --input_type image_tensor \
            --pipeline_config_path pipeline_proto/pipeline.config \
            --trained_checkpoint_dir /tmp/outputs \
            --output_directory /tmp/servable/ && \
		 mkdir /tmp/servable/saved_model/1 &&  \
		 mv /tmp/servable/saved_model/* /tmp/servable/saved_model/1/"

configure-labelbox:
	cd observe-svc && python3 configure_project.py

configure-storage:
	cd storage/config && ./configure.sh

build-svcs:
	@eval $$(minikube docker-env) ;\
	docker-compose build

deploy:
	#./deployment/create_secret.sh
	#nohup ./deployment/mount_drives.sh &
	kubectl apply -f deployment/inference-server-deployment.yaml,deployment/observe-svc-service.yaml,deployment/storage-service.yaml,deployment/inference-svc-service.yaml,deployment/observe-svc-deployment.yaml,deployment/inference-server-service.yaml,deployment/inference-svc-deployment.yaml,deployment/storage-deployment.yaml
	./deployment/observe-metrics.sh
	#TODO: Wait for pods to initialize
	#nohup ./deployment/fwd-svc.sh > fwd.out &

start-minikube:
	minikube start

stop-minikube:
	minikube stop
	minikube delete

#Does everything except the training and directory config
build-all: start-minikube build-svcs deploy

rebuild: stop-minikube build-all




