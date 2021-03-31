kubectl apply -f observe_manifest.yaml
kubectl -n observe create secret generic credentials \
  --from-literal=customer=$OBSERVE_CUSTOMER_ID \
  --from-literal=token=$OBSERVE_TOKEN
