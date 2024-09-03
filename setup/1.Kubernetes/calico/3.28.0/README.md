Upgrading: this is the case of using operator
https://docs.tigera.io/calico/latest/operations/upgrading/kubernetes-upgrade#upgrading-an-installation-that-uses-the-operator

Download the manifest
curl https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/tigera-operator.yaml -O

Initiate an upgrade
kubectl apply --server-side --force-conflicts -f tigera-operator.yaml

Replace calicoctl
https://docs.tigera.io/calico/latest/operations/calicoctl/install
