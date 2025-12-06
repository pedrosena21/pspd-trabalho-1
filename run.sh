#!/bin/bash

# 4. Criar os deployments e services
echo "📦 Aplicando os manifests do Kubernetes..."
kubectl apply -f k8s/deployments.yaml
kubectl apply -f k8s/services.yaml

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
echo "✅ Ingress habilitado."

# 6. Criar o recurso de ingress
kubectl apply -f k8s/ingress.yaml

# 8. Mostrar status dos pods e serviços
echo "📊 Status atual:"
kubectl get pods -o wide
kubectl get svc
kubectl get ingress

echo "✅ Deploy concluído!"
