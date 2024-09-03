# IMMAD
Informatics for Molecules and MAterials Discovery (IMMAD) is a project aiming at developing a framework for data accumulation in combination with materials prediction/modeling and high-throughput numerical simulations for materials science.

# Installation
We rely on [AiiDA](https://www.aiida.net/) and [AiiDAlab](https://www.aiidalab.net/) for the development of IMMAD. You may read the documentation of AiiDA, AiiDAlab and also [JupyterHub](https://jupyter.org/hub)for further information about the deployment process.

**Note**: This instruction is not complete yet. There are several hard-coded parameters that you will have to modify. Moreover, you need to rebuild Docker images and push them to another Docker Hub repository for deployment. 

## Deploy IMMAD
There are 7 steps for setting up an on-premise Kubernetes cluster and deploying IMMAD on that on-premise cluster described in detail in the `setup` directory. For commercial clouds, the deployment process is then straighforward.

## IMMAD abstract template
We have some very basic abstract template for developing our applications. If you wish to use, simply run
```
pip install -e immad
```
