#!/bin/bash

RELEASE=immad

helm upgrade --install $RELEASE jupyterhub/jupyterhub \
    --version=3.1.0 \
    --values config.yaml \
    --cleanup-on-fail \
    --namespace immad \
    --create-namespace

kubectl delete networkpolicy/singleuser -n immad
