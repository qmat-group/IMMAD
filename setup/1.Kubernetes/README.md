# Installation

## Container Runtimes

Here we use Docker Engine. On each node of the cluster, do the following

### Configuration before installing Docker Engine

- Forwarding IPv4 and letting iptables see bridged traffic
```
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter
```

- sysctl params required by setup, params persist across reboots
```
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
```

- Apply sysctl params without reboot
```
sudo sysctl --system
```

- Check if all the above settings work
```
lsmod | grep br_netfilter
lsmod | grep overlay
sysctl net.bridge.bridge-nf-call-iptables net.bridge.bridge-nf-call-ip6tables net.ipv4.ip_forward
```

### Install Container Runtime

We use Docker Engine: check Docker Engine for CentOS 7 (as for PIAS Cluster). The CRI to be used is `containerd` which is installed together with Docker Engine.

- Remove existing Docker Engine
```
sudo yum remove docker \
                docker-client \
                docker-client-latest \
                docker-common \
                docker-latest \
                docker-latest-logrotate \
                docker-logrotate \
                docker-engine
```

- Setup Docker repository
```
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
```

- Install again Docker Engine, containerd and Docker Compose
```
sudo yum install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

- As we use `systemd` for PIAS Cluster, it will be used by k8s (`kubelet`) by default (version 1.28). However, we still need to configure the container runtime (`containerd`) to use `systemd`. To use the systemd cgroup driver in `/etc/containerd/config.toml` with runc, set
```
[plugins]
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
    ...
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
      SystemdCgroup = true
```
- Overriding the sandbox (pause) image with `containerd` in `/etc/containerd/config.toml`
```
[plugins]
  [plugins."io.containerd.grpc.v1.cri"]
    sandbox_image = "registry.k8s.io/pause:3.2"
```

- If there is `disabled_plugins = ["cri"]` in `/etc/containerd/config.toml`, then comment it 

- Start the daemons
```
sudo systemctl enable docker
sudo systemctl enable containerd
sudo systemctl start docker
sudo systemctl start containerd
```


## Install `kubeadm`

- Turn off swap
  - Temporarily: `swap off -a`
  - Permanently: disable swap mounting in `/etc/fstab`

- Set SELinux to `permissive`
```
# Set SELinux in permissive mode (effectively disabling it)
sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/' /etc/selinux/config
```

- Prepare YUM repository
```
# This overwrites any existing configuration in /etc/yum.repos.d/kubernetes.repo
cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.28/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.28/rpm/repodata/repomd.xml.key
exclude=kubelet kubeadm kubectl cri-tools kubernetes-cni
EOF
```

- Install `kubeadm, kubelet, kubectl` on all machines
```
sudo yum install -y kubelet kubeadm kubectl --disableexcludes=kubernetes
sudo systemctl enable --now kubelet
```

# Initialize the cluster with `kubeadm`

- Initialize the Kubernetes cluster on the control-plane
```
kubeadm init --pod-network-cidr=20.1.0.0/16
```
then save the line `kubeadm join ...` for later use.

- Configure to manage cluster as a regular user
```
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/PSQL_ROOT.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

- Install a Pod network (CNI) to the cluster. In our case, we use Calico
```
kubectl create -f ./calico/tigera-operator.yaml
kubectl create -f ./calico/custom-resources.yaml
```
where these .yaml are given and located in the `calico` directory. 
Then observe the status of Calico until all the pods are in the Running status, especially the CoreDNS Pod
```
watch kubectl get pods -n calico-system
```

- Join workers node into the cluster by accessing to each node and run
```
kubeadm join <control-plane-host>:<control-plane-port> --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```
The exact values for this command is shown after running `kubeadm init`.
