#!/bin/bash

echo "=========================================="
echo "Gerando código gRPC"
echo "=========================================="

mkdir -p service-a-python service-b-python stub-cpp/generated examples/generated

echo "[1/3] Gerando Python para exemplos..."
python3 -m grpc_tools.protoc \
    -I./proto \
    --python_out=./examples/generated \
    --grpc_python_out=./examples/generated \
    ./proto/examples.proto

echo "[2/3] Gerando Python para serviços..."
python3 -m grpc_tools.protoc \
    -I./proto \
    --python_out=./service-a-python \
    --grpc_python_out=./service-a-python \
    ./proto/bingo.proto

python3 -m grpc_tools.protoc \
    -I./proto \
    --python_out=./service-b-python \
    --grpc_python_out=./service-b-python \
    ./proto/bingo.proto

echo "[3/3] Gerando C++ para stub..."
protoc \
    -I./proto \
    --cpp_out=./stub-cpp/generated \
    --grpc_out=./stub-cpp/generated \
    --plugin=protoc-gen-grpc=`which grpc_cpp_plugin` \
    ./proto/bingo.proto

echo "✓ Concluído!"
