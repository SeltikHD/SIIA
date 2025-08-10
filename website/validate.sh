#!/bin/bash

# Script de validação do setup Docker para SIIA
echo "🔍 === VALIDAÇÃO DO SETUP SIIA ==="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
CHECKS_PASSED=0
CHECKS_TOTAL=0

# Função para check
check_item() {
    local description="$1"
    local command="$2"
    local is_required="$3"
    
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    
    echo -n "Verificando $description... "
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        if [ "$is_required" = "required" ]; then
            echo -e "${RED}❌ FALHOU${NC}"
        else
            echo -e "${YELLOW}⚠️  OPCIONAL${NC}"
        fi
        return 1
    fi
}

# Função para verificar arquivo
check_file() {
    local file="$1"
    local description="$2"
    local is_required="$3"
    
    check_item "$description" "[ -f '$file' ]" "$is_required"
}

# Função para verificar comando
check_command() {
    local cmd="$1"
    local description="$2"
    local is_required="$3"
    
    check_item "$description" "command -v $cmd" "$is_required"
}

echo ""
echo "🔧 === FERRAMENTAS NECESSÁRIAS ==="

# Docker
check_command "docker" "Docker" "required"
if ! command -v docker >/dev/null 2>&1; then
    echo -e "${RED}   Instale Docker: sudo apt install docker.io${NC}"
fi

# Docker Compose
if command -v docker >/dev/null 2>&1; then
    check_item "Docker Compose" "docker compose version" "required"
    if ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}   Instale Docker Compose ou use versão mais recente do Docker${NC}"
    fi
fi

# Docker rodando
check_item "Docker daemon" "docker info" "required"
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}   Inicie Docker: sudo systemctl start docker${NC}"
fi

# Node.js (opcional para desenvolvimento local)
check_command "node" "Node.js" "optional"
check_command "npm" "NPM" "optional"

# Python (opcional para desenvolvimento local)
check_command "python3" "Python 3" "optional"
check_command "pip3" "pip3" "optional"

echo ""
echo "📄 === ARQUIVOS DE CONFIGURAÇÃO ==="

# Arquivos obrigatórios
check_file "docker-compose.yml" "Docker Compose" "required"
check_file "Dockerfile.web" "Dockerfile Web" "required" 
check_file ".env" "Arquivo .env" "required"
check_file "app.py" "Aplicação Flask" "required"
check_file "requirements.txt" "Dependências Python" "required"
check_file "package.json" "Configuração Node.js" "required"

# Arquivos de banco
check_file "init.sql" "Script de inicialização DB" "required"
check_file "model.sql" "Dados de exemplo DB" "optional"

# Scripts
check_file "setup.sh" "Script de setup" "optional"
check_file "db-init.sh" "Script de init DB" "optional"
check_file "db-rm.sh" "Script de limpeza" "optional"

echo ""
echo "🔐 === CONFIGURAÇÃO .env ==="

if [ -f ".env" ]; then
    # Verifica variáveis importantes
    while IFS= read -r line; do
        if [[ $line =~ ^[A-Z_]+=.+ ]]; then
            var_name=$(echo "$line" | cut -d'=' -f1)
            var_value=$(echo "$line" | cut -d'=' -f2-)
            
            case $var_name in
                "DATABASE_URL")
                    if [[ $var_value =~ postgresql:// ]]; then
                        echo -e "✅ DATABASE_URL: ${GREEN}Configurado${NC}"
                        CHECKS_PASSED=$((CHECKS_PASSED + 1))
                    else
                        echo -e "❌ DATABASE_URL: ${RED}Formato inválido${NC}"
                    fi
                    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
                    ;;
                "SECRET_KEY")
                    if [ ${#var_value} -gt 20 ]; then
                        echo -e "✅ SECRET_KEY: ${GREEN}Configurado${NC}"
                        CHECKS_PASSED=$((CHECKS_PASSED + 1))
                    else
                        echo -e "❌ SECRET_KEY: ${RED}Muito curto${NC}"
                    fi
                    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
                    ;;
                "SMTP_USERNAME")
                    if [ ! -z "$var_value" ]; then
                        echo -e "✅ SMTP_USERNAME: ${GREEN}Configurado${NC}"
                        CHECKS_PASSED=$((CHECKS_PASSED + 1))
                    else
                        echo -e "⚠️  SMTP_USERNAME: ${YELLOW}Não configurado (opcional)${NC}"
                    fi
                    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
                    ;;
            esac
        fi
    done < .env
else
    echo -e "${RED}❌ Arquivo .env não encontrado${NC}"
fi

echo ""
echo "🐳 === TESTE DOCKER ==="

# Testa se consegue fazer pull de uma imagem
check_item "Conectividade Docker Hub" "docker pull hello-world" "required"

# Verifica permissões Docker
if command -v docker >/dev/null 2>&1; then
    if groups | grep -q docker; then
        echo -e "✅ Permissões Docker: ${GREEN}Usuário no grupo docker${NC}"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo -e "⚠️  Permissões Docker: ${YELLOW}Adicione usuário ao grupo docker${NC}"
        echo -e "${YELLOW}   sudo usermod -aG docker \$USER${NC}"
    fi
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
fi

echo ""
echo "📱 === APLICATIVO MÓVEL ==="

# Verifica arquivos do móvel
check_file "mobile/main_app.py" "App móvel principal" "optional"
check_file "mobile/requirements.txt" "Dependências móvel" "optional"
check_file "mobile/Dockerfile.mobile" "Dockerfile móvel" "optional"

# X11 para GUI (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    check_item "X11 para GUI" "[ ! -z \"\$DISPLAY\" ]" "optional"
    if [ -z "$DISPLAY" ]; then
        echo -e "${YELLOW}   Para app móvel: export DISPLAY=:0${NC}"
    fi
fi

echo ""
echo "🎯 === RESUMO DA VALIDAÇÃO ==="

PERCENTAGE=$((CHECKS_PASSED * 100 / CHECKS_TOTAL))

echo -e "Verificações: ${CHECKS_PASSED}/${CHECKS_TOTAL} (${PERCENTAGE}%)"

if [ $PERCENTAGE -ge 90 ]; then
    echo -e "${GREEN}🎉 Setup excelente! Projeto pronto para execução.${NC}"
    STATUS="excellent"
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "${YELLOW}⚠️  Setup bom, mas pode melhorar algumas configurações.${NC}"
    STATUS="good"
else
    echo -e "${RED}❌ Setup incompleto. Corrija os problemas antes de continuar.${NC}"
    STATUS="poor"
fi

echo ""
echo "🚀 === PRÓXIMOS PASSOS ==="

case $STATUS in
    "excellent")
        echo -e "${GREEN}✅ Tudo pronto! Execute:${NC}"
        echo "   ./setup.sh"
        echo "   OU"
        echo "   docker compose up"
        ;;
    "good") 
        echo -e "${YELLOW}⚠️  Corrija configurações opcionais:${NC}"
        echo "   1. Configure variáveis faltantes no .env"
        echo "   2. Execute: ./setup.sh"
        ;;
    "poor")
        echo -e "${RED}❌ Ações necessárias:${NC}"
        echo "   1. Instale Docker se não tiver"
        echo "   2. Configure arquivo .env"
        echo "   3. Verifique arquivos obrigatórios"
        echo "   4. Execute novamente este script"
        ;;
esac

echo ""
echo "📚 === DOCUMENTAÇÃO ==="
echo "   🐳 Docker: DOCKER.md"
echo "   📱 Mobile: mobile/README.md"
echo "   🌐 Web: README.md"

exit 0
