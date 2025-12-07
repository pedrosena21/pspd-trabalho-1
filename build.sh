#!/bin/bash

TAG="undefined"

echo "Realizando build"
docker compose build

arch=$(uname -m)
case "$arch" in
  x86_64|amd64)
    echo "Arquitetura x86_64"
    TAG="latest"
	;;
  aarch64|arm64)
    echo "Arquitetura ARM"
    TAG="rpi"
	;;
  *)
esac


docker tag stub-node:latest "$DOCKERHUB_USERNAME/stub-node:$TAG"
docker tag service-a-python:latest "$DOCKERHUB_USERNAME/service-a-python:$TAG"
docker tag service-b-python:latest "$DOCKERHUB_USERNAME/service-b-python:$TAG"

echo "Login no Docker Hub"
echo" $DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin

echo "Subindo Imagens"
docker push "$DOCKERHUB_USERNAME/stub-node:$TAG"
docker push "$DOCKERHUB_USERNAME/service-a-python:$TAG"
docker push "$DOCKERHUB_USERNAME/service-b-python:$TAG"

