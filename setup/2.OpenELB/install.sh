# OpenELB
helm repo add kubesphere-stable https://charts.kubesphere.io/stable
helm repo update
kubectl create ns openelb-system
helm install openelb kubesphere-stable/openelb -n openelb-system
