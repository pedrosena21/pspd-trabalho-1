#!/bin/bash

set -e

echo "🚀 Iniciando deploy do projeto no Minikube..."

# 1. Iniciar o minikube
echo "👉 Iniciando o Minikube..."
minikube start

# 2. Apontar o Docker CLI para o Docker interno do Minikube
echo "👉 Usando o Docker interno do Minikube..."
eval $(minikube docker-env)

# 3. Buildar as imagens localmente
echo "🐳 Buildando imagens Docker..."
docker compose build

# 4. Criar os deployments e services
echo "📦 Aplicando os manifests do Kubernetes..."
kubectl apply -f k8s/deployments.yaml
kubectl apply -f k8s/services.yaml

# 5. Habilitar o Ingress
echo "🌐 Habilitando o Ingress..."
minikube addons enable ingress

# 6. Criar o recurso de ingress
kubectl apply -f k8s/ingress.yaml

# 7. Adicionar o host no /etc/hosts
MINIKUBE_IP=$(minikube ip)
HOST_ENTRY="$MINIKUBE_IP bingo-api"

if ! grep -q "bingo-api" /etc/hosts; then
  echo "🧩 Adicionando entrada no /etc/hosts..."
  echo "$HOST_ENTRY" | sudo tee -a /etc/hosts > /dev/null
else
  echo "✅ Entrada do host já existe."
fi

# 8. Mostrar status dos pods e serviços
echo "📊 Status atual:"
kubectl get pods -o wide
kubectl get svc
kubectl get ingress

echo "✅ Deploy concluído!"
echo "🌍 Acesse: http://bingo-api/docs"
