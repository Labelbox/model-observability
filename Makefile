
configure-labelbox:
	cd services/ && \
		python3 -m resources.configure

configure-storage:
	cd services/storage_svc && ./configure.sh

download-model:
	python3 scripts/download_model.py

