FROM ubuntu:22.04

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgrpc++-dev \
    libprotobuf-dev \
    protobuf-compiler-grpc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos gerados do proto
COPY generated/ /app/generated/

# Copiar código fonte
COPY server.cpp /app/
COPY CMakeLists.txt /app/

# Compilar
RUN mkdir build && cd build && \
    cmake .. && \
    make

# Expor porta HTTP
EXPOSE 8080

# Comando para executar
CMD ["./build/bingo_stub", "--game-service", "service-a:50051", "--validation-service", "service-b:50052", "--port", "8080"]
