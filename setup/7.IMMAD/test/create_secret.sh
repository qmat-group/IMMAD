kubectl create ns hinit
kubectl create secret generic hinit-cred \
    --from-file=.dockerconfigjson=$HOME/.docker/config.json \
    --type=kubernetes.io/dockerconfigjson \
    --namespace=hinit
