#!/bin/bash

set -e

echo "🔄 Atualizando configurações de rede e aplicação..."
# Reaplica services e deployments da aplicação
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/deployments.yaml

echo "📊 Deployando Prometheus e Grafana no Minikube..."

# 1. Aplicar ConfigMap do Prometheus
echo "👉 Criando ConfigMap do Prometheus..."
kubectl apply -f k8s/prometheus-configmap.yaml

# 2. Aplicar Deployment e Service do Prometheus
echo "👉 Deployando Prometheus..."
kubectl apply -f k8s/prometheus-deployment.yaml

# 3. Reiniciar o deployment para garantir que pegue o ConfigMap atualizado
echo "🔄 Atualizando configuração do Prometheus..."
kubectl rollout restart deployment/prometheus-deployment || true

# 4. Aplicar Deployment e Service do Grafana
echo "👉 Deployando Grafana..."
kubectl apply -f k8s/grafana-deployment.yaml

# Aguardar os pods ficarem prontos
echo "⏳ Aguardando pods de monitoramento..."
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=grafana --timeout=120s || true

# Obter o IP do Minikube
MINIKUBE_IP=$(minikube ip)

echo ""
echo "✅ Monitoramento atualizado!"
echo "   Agora monitorando: stub-node (8080) e game-service (8001)"
echo ""
echo "📊 Acesse os serviços:"
echo "   Prometheus: http://$MINIKUBE_IP:30090"
echo "   Grafana:    http://$MINIKUBE_IP:30300"
echo ""
echo "🔐 Credenciais do Grafana:"
echo "   Usuário: admin"
echo "   Senha:   admin"
echo ""
echo "📈 Para verificar o status:"
echo "   kubectl get pods -l app=prometheus"
echo "   kubectl get pods -l app=grafana"
echo "   kubectl get svc prometheus-service grafana-service"

