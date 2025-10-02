FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY game_service.py .
COPY bingo_pb2.py .
COPY bingo_pb2_grpc.py .

EXPOSE 50051

CMD ["python", "game_service.py"]
