#!/bin/bash

set -e

echo "📊 Deployando Prometheus e Grafana no Minikube..."

# Aplicar ConfigMap do Prometheus
echo "👉 Criando ConfigMap do Prometheus..."
kubectl apply -f k8s/prometheus-configmap.yaml

# Aplicar Deployment e Service do Prometheus
echo "👉 Deployando Prometheus..."
kubectl apply -f k8s/prometheus-deployment.yaml

# Aplicar Deployment e Service do Grafana
echo "👉 Deployando Grafana..."
kubectl apply -f k8s/grafana-deployment.yaml

# Aguardar os pods ficarem prontos
echo "⏳ Aguardando pods ficarem prontos..."
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=90s || true
kubectl wait --for=condition=ready pod -l app=grafana --timeout=90s || true

# Obter o IP do Minikube
MINIKUBE_IP=$(minikube ip)

echo ""
echo "✅ Deploy concluído!"
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

