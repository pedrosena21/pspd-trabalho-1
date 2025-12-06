FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Instala dependências básicas necessárias para compilar dependências Python se preciso
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instala Locust e requests (locust irá instalar suas dependências)
RUN pip install --no-cache-dir locust requests grpcio protobuf

WORKDIR /app

# Copia apenas o diretório de testes (construa com o contexto correto)
COPY . /app

# Porta padrão do web UI do Locust
EXPOSE 8089

ENTRYPOINT ["locust"]
CMD ["-f", "http_test.py", "--host", "http://bingo-api:80"]
CMD ["-f", "service-a_test.py", "--host", "http://bingo-api:50051"]
CMD ["-f", "service-b_test.py", "--host", "http://bingo-api:50052"]
