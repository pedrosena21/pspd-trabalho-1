#!/bin/bash

echo "Criando Deploys e Services"
kubectl apply -f k8s/deployments.yaml
kubectl apply -f k8s/services.yaml

echo "Aguardando Pods ficarem prontos"
kubectl wait --for=condition=ready pod -l app=stub-node --timeout=90s || true
kubectl wait --for=condition=ready pod -l app=game-server --timeout=90s || true
kubectl wait --for=condition=ready pod -l app=validation-server --timeout=90s || true

echo "Criando Ingress"
kubectl apply -f k8s/ingress.yaml

# 8. Mostrar status dos pods e serviços
echo "Status atual"
kubectl get pods -o wide
kubectl get svc
kubectl get ingress

echo "Deploy concluído!"
