FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY validation_service.py .
COPY bingo_pb2.py .
COPY bingo_pb2_grpc.py .

EXPOSE 50052

CMD ["python", "validation_service.py"]
