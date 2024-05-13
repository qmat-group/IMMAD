# Setup persistent storage using NFS

- Install `nfs-subdir-external-provisioner`
```
helm install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
    --set nfs.server=10.1.1.1 \
    --set nfs.path=/export/k8s
```

- Setup storage class corresponding to NFS provisioner
```
kubectl patch storageclass nfs-client -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
