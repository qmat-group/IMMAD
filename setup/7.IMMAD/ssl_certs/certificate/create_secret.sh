#!/bin/bash

# Your SSL certificate is stored in $CERT_DIR directory
CERT_DIR=./cert

PRIV_KEY=$CERT_DIR/privkey.pem
CERT=$CERT_DIR/cert.pem

kubectl delete secret immad-cert -n immad
kubectl create secret tls immad-cert -n immad --key=$PRIV_KEY --cert=$CERT -o yaml
