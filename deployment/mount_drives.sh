
minikube mount $(pwd)/../:/data &
minikube mount /tmp/servable/saved_model:/models/animaldet &
minikube mount $(pwd)/../storage:/host/storage
