# pspd-trabalho-1

## Requisitos para rodar

### KUBECTL

Client Version: v1.34.1

Kustomize Version: v5.7.1

Server Version: v1.34.0

### minikube version: v1.37.0

### Docker 28.4.0

## COMO RODAR

### Backend

```chmod +x run.sh stop.sh```

```./run.sh```

### Frontend

```docker build -t bingo_frontend frontend/```

```docker run -p 3000:80 bingo_frontend```



## Como parar e reverter alterações do docker

```./stop.sh```