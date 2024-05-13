# Deploy RabbitMQ server

- Create the namespace for RabbitMQ
```
kubectl create namespace rabbitmq
```

- Add Helm repository for RabbitMQ
```
helm repo add bitnami https://charts.bitnami.com/bitnami
```

- Deploy RabbitMQ using Helm 
```
helm install rabbitmq bitnami/rabbitmq-cluster-operator -n rabbitmq --atomic
```

- Create RabbitMQ cluster
```
kubectl apply -f cluster.yaml
``` 
