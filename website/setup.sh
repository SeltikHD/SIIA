#!/bin/bash

# Script de configuração inicial do projeto SIA2
echo "🚀 === SETUP INICIAL DO PROJETO SIA2 ==="

# Função para gerar secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_hex(64))" 2>/dev/null || \
    openssl rand -hex 64 2>/dev/null || \
    echo "CHANGE_THIS_SECRET_KEY_$(date +%s)"
}

# Verifica se o Docker está instalado e rodando
echo "🐳 Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Instale o Docker e tente novamente."
    echo "   Ubuntu/Debian: sudo apt install docker.io docker-compose"
    echo "   CentOS/RHEL: sudo yum install docker docker-compose"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker não está rodando. Inicie o serviço Docker:"
    echo "   sudo systemctl start docker"
    exit 1
fi

echo "✅ Docker está disponível"

# Verifica se o Node.js está disponível (para desenvolvimento local)
if command -v node &> /dev/null; then
    echo "✅ Node.js está disponível ($(node --version))"
else
    echo "⚠️  Node.js não encontrado localmente, mas será usado via container"
fi

# Configura arquivo .env
echo ""
echo "📝 === CONFIGURAÇÃO DO AMBIENTE ==="

if [ -f ".env" ]; then
    echo "📄 Arquivo .env já existe"
    read -p "Deseja reconfigurar? [s/N]: " RECONFIG
    RECONFIG=${RECONFIG:-n}
    
    if [[ ! $RECONFIG =~ ^[Ss]$ ]]; then
        echo "✅ Mantendo configuração existente"
        ENV_CONFIGURED=true
    fi
fi

if [ "$ENV_CONFIGURED" != "true" ]; then
    echo "🔧 Configurando arquivo .env..."
    
    # Copia exemplo se não existir
    if [ ! -f ".env" ] && [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📋 Base copiada de .env.example"
    fi
    
    # Solicita configurações principais
    echo ""
    echo "🔐 === CONFIGURAÇÃO DO BANCO DE DADOS ==="
    read -p "Nome do banco [siia]: " DB_NAME
    DB_NAME=${DB_NAME:-siia}
    
    read -p "Usuário do banco [lopinhos]: " DB_USER
    DB_USER=${DB_USER:-lopinhos}
    
    read -s -p "Senha do banco [senha123]: " DB_PASSWORD
    DB_PASSWORD=${DB_PASSWORD:-senha123}
    echo ""
    
    # Gera SECRET_KEY se não existir
    echo "🔑 Gerando chave secreta..."
    SECRET_KEY=$(generate_secret_key)
    
    # Configurações de email (opcionais)
    echo ""
    echo "📧 === CONFIGURAÇÃO DE EMAIL (opcional) ==="
    read -p "Servidor SMTP [smtp.gmail.com]: " SMTP_SERVER
    SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}
    
    read -p "Porta SMTP [587]: " SMTP_PORT
    SMTP_PORT=${SMTP_PORT:-587}
    
    read -p "Email para recuperação de senha (opcional): " SMTP_USERNAME
    
    if [ ! -z "$SMTP_USERNAME" ]; then
        read -s -p "Senha do email (ou app password): " SMTP_PASSWORD
        echo ""
    fi
    
    # Cria ou atualiza .env
    cat > .env << EOF
# Configuração do banco de dados
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}

# Chave secreta do Flask
SECRET_KEY=${SECRET_KEY}

# API Key Trefle (opcional)
TREFLE_API_KEY=VGT5KTyQ6O0E59qbYGqucYao61AzAJm6yMuB9oN9zUI

# Credenciais do usuário admin
ADMIN_USERNAME=admin@siia.ifpb.edu.br
ADMIN_PASSWORD=SIIA@AdminPassword

# Configurações SMTP para envio de emails
SMTP_SERVER=${SMTP_SERVER}
SMTP_PORT=${SMTP_PORT}
SMTP_USERNAME=${SMTP_USERNAME}
SMTP_PASSWORD=${SMTP_PASSWORD}

# URL do site
SITE_URL=http://localhost:5000
EOF
    
    echo "✅ Arquivo .env configurado!"
fi

# Verifica arquivos necessários
echo ""
echo "📋 === VERIFICANDO ARQUIVOS NECESSÁRIOS ==="

required_files=(
    "docker-compose.yml"
    "Dockerfile.web"
    "init.sql"
    "app.py"
    "requirements.txt"
    "package.json"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (não encontrado)"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "❌ Arquivos obrigatórios não encontrados:"
    printf '   %s\n' "${missing_files[@]}"
    echo "Certifique-se de estar no diretório correto do projeto."
    exit 1
fi

# Oferece opções de inicialização
echo ""
echo "🎯 === OPÇÕES DE INICIALIZAÇÃO ==="
echo "1. Apenas banco de dados"
echo "2. Projeto completo (web + banco)"
echo "3. Projeto completo + móvel"
echo ""

read -p "Escolha uma opção [2]: " OPTION
OPTION=${OPTION:-2}

case $OPTION in
    1)
        echo "🚀 Iniciando apenas o banco de dados..."
        ./db-init.sh
        ;;
    2)
        echo "🚀 Iniciando projeto completo..."
        docker compose up -d
        echo ""
        echo "✅ Projeto iniciado!"
        echo "🌐 Acesse: http://localhost:5000"
        echo "📊 Logs: docker compose logs -f"
        ;;
    3)
        echo "🚀 Iniciando projeto completo com móvel..."
        docker compose --profile mobile up -d
        echo ""
        echo "✅ Projeto iniciado com app móvel!"
        echo "🌐 Web: http://localhost:5000"
        echo "📱 Mobile: docker compose exec mobile python main_app.py"
        echo "📊 Logs: docker compose logs -f"
        ;;
    *)
        echo "❌ Opção inválida"
        exit 1
        ;;
esac

echo ""
echo "🎉 === SETUP CONCLUÍDO ==="
echo ""
echo "📋 Comandos úteis:"
echo "   docker compose up          # Iniciar tudo"
echo "   docker compose down        # Parar tudo"
echo "   docker compose logs -f     # Ver logs"
echo "   ./db-rm.sh                 # Limpeza completa"
echo ""
echo "📱 Para o app móvel:"
echo "   docker compose --profile mobile up"
echo "   docker compose exec mobile python main_app.py"
