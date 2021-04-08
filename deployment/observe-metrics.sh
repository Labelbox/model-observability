kubectl apply -f deployment/observe_manifest.yaml
kubectl -n observe delete secret credentials --ignore-not-found
kubectl -n observe create secret generic credentials \
  --from-literal=customer=$OBSERVE_CUSTOMER_ID \
  --from-literal=token=$OBSERVE_TOKEN


