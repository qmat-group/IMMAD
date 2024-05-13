# Ingress Controller

We use `ingress-nginx` as the Ingress controller

## Install `ingress-nginx` using Helm

```
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

## Install the Load Balancer service using the given YAML file
```
kubectl apply -f ingress-nginx-controller.yaml
```

Note that in this file, the Load Balancer external IP is specified directly in `externalIPs`.
