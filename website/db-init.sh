#!/bin/bash

# Pede os dados ao usuário
read -p "Digite o nome do banco de dados: " DB_NAME
read -p "Digite o nome do usuário: " DB_USER
read -s -p "Digite a senha do usuário: " DB_PASSWORD
echo

# Define nomes de volume e container
VOLUME_NAME=pgdata
CONTAINER_NAME=postgres-container

# Verifica se o init.sql existe
if [ ! -f "./init.sql" ]; then
    echo "Erro: Arquivo init.sql não encontrado na pasta atual."
    exit 1
fi

# Cria o volume (ignora se já existir)
podman volume inspect $VOLUME_NAME >/dev/null 2>&1 || podman volume create $VOLUME_NAME

# Roda o container
podman run -d \
    --name $CONTAINER_NAME \
    -e POSTGRES_DB=$DB_NAME \
    -e POSTGRES_USER=$DB_USER \
    -e POSTGRES_PASSWORD=$DB_PASSWORD \
    -p 5432:5432 \
    -v $VOLUME_NAME:/var/lib/postgresql/data \
    -v ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro \
    docker.io/library/postgres:15

echo "PostgreSQL iniciado com sucesso!"
echo "Banco: $DB_NAME | Usuário: $DB_USER"
