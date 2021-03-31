
minikube mount $(pwd)/../:/data &
minikube mount $(pwd)/../animal-svc/servable/saved_model:/models/animaldet &
minikube mount $(pwd)/../storage:/host/storage
#- .:/data/
#- ./animal-svc/servable/saved_model:/models/animaldet
#- ./storage:/home/sirius/data

