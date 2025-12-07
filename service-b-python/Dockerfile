FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY validation_service.py .
COPY bingo_pb2.py .
COPY bingo_pb2_grpc.py .

# 50052 = gRPC Server
# 8002  = Prometheus Metrics (Validation Service)
EXPOSE 50052 8002

CMD ["python", "validation_service.py"]