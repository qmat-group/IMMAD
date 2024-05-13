# Deploy IMMAD

## Build Docker images

We use two different images.

1. `init-user` image for `initContainers`. This `init-user` runs first to initialize the PostgreSQL database and user, the RabbitMQ server and prepare an YAML file to setup AiiDA profile later on.

2. `immad` image is the main image for IMMAD. Based on JupyterHub image, we install in it AiiDA and AiiDAlab, prepare scripts to run after deploying the Docker image (install additional packages, initialize AiIDA, etc.) 

`Dockerfile`s for these images are stored somewhere else.

## Get RabbitMQ default username and password

- Username
```
kubectl get secret rabbitmq-cluster-default-user -o jsonpath="{.data.username}" -n rabbitmq | base64 -d
```

- Password
```
kubectl get secret rabbitmq-cluster-default-user -n rabbitmq -o jsonpath="{.data.password}" | base64 -d
```

- In `config.yaml` of IMMAD, paste these username and password into `singleuser.initContainers.args` as
args: ['/immad/init.sh', '{unescaped_username}', 'PSQL_PASSWORD', '/var/immad', USERNAME, PASSWORD]

## Certificate and Ingress
We are unable to use `cert-manager` (failed when doing HTTP01 ACME challenge), therefore, we switch to using certificate provided by a CA (or even use certificate provided by Let's Encrypt).

- First, go the the directory `./ssl_certs/certificate`

- Create IMMAD namespace
```
kubectl create namespace immad
```

- Import the certificate and its key as k8s TLS secret: one needs to edit the `create_secret.sh` to point out the appropriate directory storing the certificate. Then run the script
```
sh create_secret.sh
```

- Setup the Ingress object
```
kubectl apply -f ingress.yml
```

## Run IMMAD

- Generate secret containing credentials for accessing IMMAD Docker Hub account
```
kubectl create secret generic immad-cred \
    --from-file=.dockerconfigjson=$HOME/.docker/config.json \
    --type=kubernetes.io/dockerconfigjson \
    --namespace=immad
```

- Deploy IMMAD
```
helm upgrade --install immad jupyterhub/jupyterhub \
    --version=3.1.0 \
    --values config.yaml \
    --cleanup-on-fail \
    --namespace immad \
    --create-namespace
```

## Configure Network Policy

In order to use in-house HPC cluster, we need to reconfigure the network policy of IMMAD deployment to allow SSH protocal between the pods and the cluster nodes.

In IMMAD (JupyterHub), there is `networkpolicy/singleuser`, which blocks SSH (as well as many other ports). We need to learn more about k8s network policy. At the present, the ad-hoc solution is to delete `networkpolicy/singleuser`.

```
kubectl delete networkpolicy/singleuser -n immad
```
