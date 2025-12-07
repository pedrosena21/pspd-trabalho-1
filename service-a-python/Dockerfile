FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 50051 = gRPC Server
# 8001  = Prometheus Metrics
EXPOSE 50051 8001

CMD ["python", "game_service.py"]
