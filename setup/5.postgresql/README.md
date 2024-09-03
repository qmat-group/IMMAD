# Deploy PostgreSQL server

- Create storage class
kubectl apply -f postgres-storage-class.yaml

- Create namespace for PostgreSQL server
```
kubectl create namespace postgres
```

- Create secrets for PostgreSQL server containing the database name, admin user and password 
```
kubectl -n postgres create secret generic postgres-secret --from-env-file=sec-env.conf
```

- Deploy the PostgreSQL server
```
kubectl apply -f postgres-deployment.yaml
```
