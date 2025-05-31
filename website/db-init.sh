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

# Pergunta se deseja carregar dados de exemplo
read -p "Deseja carregar dados de exemplo (culturas, fertilizantes, sessões)? [s/N]: " LOAD_SAMPLE_DATA
LOAD_SAMPLE_DATA=${LOAD_SAMPLE_DATA:-n}

# Se confirmado, verifica se o model.sql existe
if [[ $LOAD_SAMPLE_DATA =~ ^[Ss]$ ]]; then
    if [ ! -f "./model.sql" ]; then
        echo "Aviso: Arquivo model.sql não encontrado. Apenas o banco será inicializado sem dados de exemplo."
        LOAD_SAMPLE_DATA="n"
    else
        echo "Dados de exemplo serão carregados do arquivo model.sql"
    fi
fi

# Cria o volume (ignora se já existir)
podman volume inspect $VOLUME_NAME >/dev/null 2>&1 || podman volume create $VOLUME_NAME

# Roda o container
if [[ $LOAD_SAMPLE_DATA =~ ^[Ss]$ ]]; then
    # Com dados de exemplo
    podman run -d \
        --name $CONTAINER_NAME \
        -e POSTGRES_DB=$DB_NAME \
        -e POSTGRES_USER=$DB_USER \
        -e POSTGRES_PASSWORD=$DB_PASSWORD \
        -p 5432:5432 \
        -v $VOLUME_NAME:/var/lib/postgresql/data \
        -v ./init.sql:/docker-entrypoint-initdb.d/01-init.sql:ro \
        -v ./model.sql:/docker-entrypoint-initdb.d/02-model.sql:ro \
        docker.io/library/postgres:15
    echo "PostgreSQL iniciado com sucesso com dados de exemplo!"
else
    # Apenas inicialização básica
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
fi
echo "Banco: $DB_NAME | Usuário: $DB_USER"
