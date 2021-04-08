kubectl delete secret keys --ignore-not-found
kubectl create secret generic keys \
    --from-literal=labelbox_api_key=$LABELBOX_API_KEY \
    --from-literal=ngrok_key=$NGROK_TOKEN
