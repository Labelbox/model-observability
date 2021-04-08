
wait_for_ready() {
    POD=$(kubectl get pods | grep $1 | grep -e "Running" -e "ContainerCreating" | awk '{print $1}')
    while [[ $(kubectl get pods $POD -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True" ]]; do
        POD=$(kubectl get pods | grep $1 | grep -e "Running" -e "ContainerCreating" | awk '{print $1}') && sleep 3; done
    echo $POD
}


kubectl port-forward pod/$(wait_for_ready "inference-svc") 5000 &
kubectl port-forward pod/$(wait_for_ready "observe-svc") 5001:5000
