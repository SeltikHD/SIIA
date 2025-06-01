#!/bin/bash

# Script simplificado para debug da função run_tests_with_retry

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para print colorido
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Função para executar testes com retry
run_tests_with_retry() {
    local test_name="$1"
    local test_command="$2"
    local max_retries=3
    local retry_count=0

    echo "DEBUG: Starting run_tests_with_retry"
    echo "DEBUG: test_name=$test_name"
    echo "DEBUG: test_command=$test_command"
    echo "DEBUG: max_retries=$max_retries"

    while [ $retry_count -lt $max_retries ]; do
        echo "DEBUG: Loop iteration $retry_count"
        print_status "Executando $test_name (tentativa $((retry_count + 1))/$max_retries)..."

        echo "DEBUG: About to execute command: $test_command"
        
        if eval "$test_command"; then
            echo "DEBUG: Command succeeded"
            print_success "$test_name executado com sucesso"
            return 0
        else
            echo "DEBUG: Command failed"
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                print_warning "$test_name falhou, tentando novamente..."
                sleep 2
            else
                print_error "$test_name falhou após $max_retries tentativas"
                return 1
            fi
        fi
    done
}

echo "🧪 DEBUG: Testing run_tests_with_retry function"
echo "=============================================="

# Teste simples primeiro
print_status "Testando com comando simples..."
if run_tests_with_retry "Teste Simples" "echo 'Hello World'"; then
    print_success "Comando simples funcionou"
else
    print_error "Comando simples falhou"
fi

echo
print_status "Testando com pytest..."

# Agora teste com pytest
if run_tests_with_retry "Testes de Modelos" "pytest tests/test_models.py -v --tb=short"; then
    print_success "Pytest funcionou"
else
    print_error "Pytest falhou"
fi

echo "DEBUG: Script concluído"
