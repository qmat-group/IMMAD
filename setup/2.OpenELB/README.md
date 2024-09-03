# Load Balancer

We use OpenELB Load Balancer for our cluster

## Install Helm for package managing

1. Download your desired version
2. Unpack it (`tar -zxvf helm-v3.0.0-linux-amd64.tar.gz`)
3. Find the helm binary in the unpacked directory, and move it to its desired destination (`mv linux-amd64/helm /usr/local/bin/helm`)

## Install OpenELB with Helm

```
helm repo add kubesphere-stable https://charts.kubesphere.io/stable
helm repo update
kubectl create ns openelb-system
helm install openelb kubesphere-stable/openelb -n openelb-system
```

## Configuration

We do not setup the Eip for IP pool for the OpenELB, instead we specify the loadBalancerIP to be used in the Ingress Controller (which is `ingress-nginx`).

### Enable strictARP for kube-proxy

As we use Layer 2 mode of OpenELB, we need to enable strictARP for kube-proxy so that OpenELB handles ARP requests instead.
- Log in to the Kubernetes cluster and run the following command to edit the kube-proxy ConfigMap:
```
kubectl edit configmap kube-proxy -n kube-system
```
- In the kube-proxy ConfigMap YAML configuration, set data.config.conf.ipvs.strictARP to true.
```
    ipvs:
      strictARP: true
```
- Run the following command to restart kube-proxy:
```
    kubectl rollout restart daemonset kube-proxy -n kube-system
```

### Specify the NIC to be used
```
kubectl annotate nodes HOSTNAME layer2.openelb.kubesphere.io/v1alpha1="IP_ADDRESS"
```
