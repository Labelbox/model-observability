
ANIMAL_POD_NAME=$(kubectl get pods | grep "animal-svc" | awk '{print $1}')
OBSERVE_POD_NAME=$(kubectl get pods | grep "observe-svc" | awk '{print $1}')
kubectl port-forward pod/$ANIMAL_POD_NAME 5000 &
kubectl port-forward pod/$OBSERVE_POD_NAME 5001:5000
