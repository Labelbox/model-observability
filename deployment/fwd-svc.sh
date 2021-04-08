INFERENCE_POD_NAME=$(kubectl get pods | grep "inference-svc" | awk '{print $1}')
OBSERVE_POD_NAME=$(kubectl get pods | grep "monitor-svc" | awk '{print $1}')


wait_for_ready() {
    while [[ $(kubectl get pods $1 -o 'jsonpath={..status.conditions[?(@.type=="Ready")].status}') != "True" ]]; do echo "waiting for pod $1" && sleep 3; done

}


wait_for_ready $INFERENCE_POD_NAME
wait_for_ready $OBSERVE_POD_NAME

kubectl port-forward pod/$INFERENCE_POD_NAME 5000 &
kubectl port-forward pod/$OBSERVE_POD_NAME 5001:5000
