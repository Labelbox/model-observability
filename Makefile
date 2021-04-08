MODEL_CMD = docker run -e LABELBOX_API_KEY=${LABELBOX_API_KEY} -p 8078:8078 -v /tmp:/tmp -u 0 -it animal_training /bin/bash -c

start-minikube:
	@x=$(minikube status | grep "Running") && if [ ! -z $x ]; then $(shell minikube start) ; fi 

build-train:
	@eval $(minikube docker-env -u) ;\
	docker build -f training/Dockerfile training/ -t animal_training

etl: build-train
	@eval $(minikube docker-env -u) ;\
	$(MODEL_CMD) "python etl.py"

train: build-train
	@eval $(minikube docker-env -u) ;\
	$(MODEL_CMD) "python train.py"
	
export: build-train
	@eval $(minikube docker-env -u) ;\
	$(MODEL_CMD) \
		"python update_protos.py && \
	     python object_detection/exporter_main_v2.py \
            --input_type image_tensor \
            --pipeline_config_path pipeline_proto/pipeline.config \
            --trained_checkpoint_dir /tmp/outputs \
            --output_directory /tmp/servable/ && \
		 mkdir /tmp/servable/saved_model/1 &&  \
		 mv /tmp/servable/saved_model/* /tmp/servable/saved_model/1/"

configure-labelbox:
	cd services/monitor-svc && \
		cp ../shared.py . && \
		python3 configure_project.py && \
		rm shared.py

configure-storage:
	cd services/storage-svc && ./configure.sh

configure-secrets: start-minikube
	./deployment/create_secret.sh
	./deployment/observe-metrics.sh
    
configure-all: configure-labelbox
    
build-svcs: start-minikube
	@eval $(minikube docker-env) ;\
	docker-compose build

deploy: start-minikube build-svcs configure-secrets
	./deployment/create_secret.sh
	nohup ./deployment/mount_drives.sh &
	kubectl apply -f deployment  
	./deployment/observe-metrics.sh
	nohup ./deployment/fwd-svc.sh > fwd.out &

clear-deploy:
	kubectl delete svc --all
	kubectl delete deployment --all
	$(shell pkill -f "minikube mount")
	$(shell pkill -f "kubetl port-forward")
	
redeploy: clear-deploy deploy 



