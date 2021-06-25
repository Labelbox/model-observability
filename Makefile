
configure-labelbox:
	cd services/ && \
		python3 -m resources.configure

configure-storage:
	cd services/storage_svc && ./configure.sh



