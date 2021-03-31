
minikube mount $(pwd)/../:/data &
minikube mount $(pwd)/../animal-svc/servable/saved_model:/models/animaldet &
minikube mount $(pwd)/../storage:/home/serius/data
#- .:/data/
#- ./animal-svc/servable/saved_model:/models/animaldet
#- ./storage:/home/sirius/data

