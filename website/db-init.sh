#!/bin/bash

# Script para inicializar o banco PostgreSQL com Docker
echo "=== INICIALIZAÇÃO DO BANCO SIIA ==="

# Verifica se o Docker está rodando
if ! docker info >/dev/null 2>&1; then
    echo "❌ Erro: Docker não está rodando. Inicie o Docker e tente novamente."
    exit 1
fi

# Verifica se o docker-compose.yml existe
if [ ! -f "./docker-compose.yml" ]; then
    echo "❌ Erro: Arquivo docker-compose.yml não encontrado na pasta atual."
    exit 1
fi

# Verifica se o .env existe
if [ ! -f "./.env" ]; then
    echo "⚠️  Arquivo .env não encontrado."
    echo "Criando .env baseado no .env.example..."
    
    if [ -f "./.env.example" ]; then
        cp .env.example .env
        echo "📝 Configure o arquivo .env com suas credenciais:"
        echo "   - DATABASE_URL (PostgreSQL)"
        echo "   - SECRET_KEY (chave secreta do Flask)"
        echo "   - SMTP_* (configurações de email)"
        echo ""
        read -p "Pressione Enter para continuar após configurar o .env..."
    else
        echo "❌ Erro: Arquivo .env.example também não encontrado."
        exit 1
    fi
fi

# Carrega variáveis do .env
if [ -f "./.env" ]; then
    echo "📄 Carregando configurações do .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Define valores padrão se não estiverem no .env
DB_NAME=${DB_NAME:-siia}
DB_USER=${DB_USER:-lopinhos}
DB_PASSWORD=${DB_PASSWORD:-senha123}

echo "🐳 Configuração do banco:"
echo "   Nome: $DB_NAME"
echo "   Usuário: $DB_USER"
echo "   Senha: [configurada]"

# Verifica se os arquivos SQL existem
if [ ! -f "./init.sql" ]; then
    echo "❌ Erro: Arquivo init.sql não encontrado na pasta atual."
    exit 1
fi

# Pergunta se deseja carregar dados de exemplo
read -p "Deseja carregar dados de exemplo (culturas, fertilizantes, sessões)? [s/N]: " LOAD_SAMPLE_DATA
LOAD_SAMPLE_DATA=${LOAD_SAMPLE_DATA:-n}

# Se confirmado, verifica se o model.sql existe
if [[ $LOAD_SAMPLE_DATA =~ ^[Ss]$ ]]; then
    if [ ! -f "./model.sql" ]; then
        echo "⚠️  Aviso: Arquivo model.sql não encontrado. Apenas o banco será inicializado sem dados de exemplo."
        LOAD_SAMPLE_DATA="n"
    else
        echo "✅ Dados de exemplo serão carregados do arquivo model.sql"
    fi
fi

# Para containers existentes
echo "🛑 Parando containers existentes..."
docker compose down

# Remove volumes se solicitado
read -p "Deseja remover dados existentes do banco? [s/N]: " RESET_DB
RESET_DB=${RESET_DB:-n}

if [[ $RESET_DB =~ ^[Ss]$ ]]; then
    echo "🗑️  Removendo volumes do banco..."
    docker compose down -v
    docker volume rm sia2_postgres_data 2>/dev/null || true
fi

# Exporta variáveis necessárias
export DB_NAME DB_USER DB_PASSWORD

# Inicia apenas o PostgreSQL
echo "🚀 Iniciando PostgreSQL..."
docker compose up -d db

# Aguarda o banco ficar pronto
echo "⏳ Aguardando PostgreSQL ficar disponível..."
timeout=60
while ! docker compose exec db pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
    sleep 2
    timeout=$((timeout - 2))
    if [ $timeout -le 0 ]; then
        echo "❌ Timeout: PostgreSQL não ficou disponível em 60 segundos."
    docker compose logs db
        exit 1
    fi
done

echo "✅ PostgreSQL está pronto!"

# Se dados de exemplo não foram carregados automaticamente, oferece opção manual
if [[ $LOAD_SAMPLE_DATA =~ ^[Ss]$ ]] && [ -f "./model.sql" ]; then
    echo "📊 Carregando dados de exemplo..."
    docker compose exec db psql -U "$DB_USER" -d "$DB_NAME" -f /docker-entrypoint-initdb.d/02-model.sql
    echo "✅ Dados de exemplo carregados!"
fi

echo ""
echo "🎉 PostgreSQL inicializado com sucesso!"
echo "📋 Informações de conexão:"
echo "   Host: localhost"
echo "   Porta: 5432"
echo "   Banco: $DB_NAME"
echo "   Usuário: $DB_USER"
echo ""
echo "🚀 Para iniciar o projeto completo, execute:"
echo "   docker compose up"
echo ""
echo "📱 Para incluir o app móvel, execute:"
echo "   docker compose --profile mobile up"
