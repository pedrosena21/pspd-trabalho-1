FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y \
    build-essential cmake pkg-config git \
    libgrpc++-dev libprotobuf-dev \
    protobuf-compiler-grpc wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN wget https://raw.githubusercontent.com/yhirose/cpp-httplib/master/httplib.h

COPY server.cpp .
COPY CMakeLists.txt .
COPY generated/ ./generated/

RUN mkdir build && cd build && cmake .. && make

FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    libgrpc++1.45 libprotobuf23 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/build/bingo_stub_server .

EXPOSE 8080

CMD ["./bingo_stub_server"]
