# pspd-trabalho-1

## COMO RODAR

- Criar e ativar ambiente virtual
`python3 -m venv venv`
`source venv/bin/activate`

- Instalar dependências
`pip install -r requirements.txt`

- Gerar código gRPC
`chmod +x generate_grpc.sh`
`./generate_grpc.sh`

- Executar os serviços em terminais separados (no ambiente virtual)

`python service-b-python/validation_service.py`

`python service-a-python/game_service.py`

`PYTHONPATH=service-a-python python test_client.py single` (ou multi no lugar de single)
