#!/bin/bash

# Script de execução completa de testes para SIA2
# Executa todos os tipos de teste e gera relatórios detalhados

# Removido set -e para permitir que testes falhos não parem o script

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

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Banner
echo "=================================================="
echo "🚀 SIA2 - Sistema de Automação de Estufa"
echo "🧪 Pipeline Completo de Testes"
echo "=================================================="
echo

# Verificar dependências
print_status "Verificando dependências..."

DEPS_OK=true

if ! command_exists python3; then
    print_error "Python 3 não encontrado!"
    DEPS_OK=false
fi

if ! command_exists pytest; then
    print_error "Pytest não encontrado! Execute: pip install -r requirements-test.txt"
    DEPS_OK=false
fi

if [ "$DEPS_OK" = false ]; then
    print_error "Dependências faltando. Abortando..."
    exit 1
fi

print_success "Dependências verificadas"

# Criar diretório de relatórios
REPORTS_DIR="reports"
mkdir -p $REPORTS_DIR
print_status "Diretório de relatórios criado: $REPORTS_DIR"

# Limpar arquivos antigos
print_status "Limpando arquivos de teste antigos..."
rm -rf htmlcov .coverage .pytest_cache
rm -f $REPORTS_DIR/*.xml $REPORTS_DIR/*.json $REPORTS_DIR/*.html

# Timestamp para relatórios
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
echo "📅 Timestamp: $TIMESTAMP" >$REPORTS_DIR/test_run_$TIMESTAMP.log

# Função para executar testes com retry
run_tests_with_retry() {
    local test_name="$1"
    local test_command="$2"
    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        print_status "Executando $test_name (tentativa $((retry_count + 1))/$max_retries)..."

        # Executar comando e capturar código de saída
        eval "$test_command"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            print_success "$test_name executado com sucesso"
            return 0
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $max_retries ]; then
                print_warning "$test_name falhou (código $exit_code), tentando novamente..."
                sleep 2
            else
                print_error "$test_name falhou após $max_retries tentativas (código $exit_code)"
                return 1
            fi
        fi
    done
}

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0

# 1. Testes de Modelos (Unitários)
echo
echo "🧪 1. TESTES DE MODELOS (UNITÁRIOS)"
echo "=================================="

if run_tests_with_retry "Testes de Modelos" "pytest tests/test_models.py -v --tb=short --junitxml=$REPORTS_DIR/models_$TIMESTAMP.xml"; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 2. Testes de Autenticação
echo
echo "🔐 2. TESTES DE AUTENTICAÇÃO"
echo "============================"

if run_tests_with_retry "Testes de Autenticação" "pytest tests/test_auth.py -v --tb=short --junitxml=$REPORTS_DIR/auth_$TIMESTAMP.xml"; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 3. Testes de Rotas Administrativas
echo
echo "👑 3. TESTES DE ROTAS ADMINISTRATIVAS"
echo "===================================="

if run_tests_with_retry "Testes Admin Routes" "pytest tests/test_admin_routes.py -v --tb=short --junitxml=$REPORTS_DIR/admin_$TIMESTAMP.xml"; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 4. Testes de Integração
echo
echo "🔗 4. TESTES DE INTEGRAÇÃO"
echo "=========================="

if run_tests_with_retry "Testes de Integração" "pytest tests/test_integration.py -v --tb=short --junitxml=$REPORTS_DIR/integration_$TIMESTAMP.xml"; then
    ((TESTS_PASSED++))
else
    ((TESTS_FAILED++))
fi

# 5. Testes com Cobertura Completa
echo
echo "📊 5. ANÁLISE DE COBERTURA"
echo "=========================="

print_status "Executando todos os testes com análise de cobertura..."

if pytest --cov=. --cov-report=html:htmlcov --cov-report=xml:$REPORTS_DIR/coverage_$TIMESTAMP.xml --cov-report=term-missing --cov-fail-under=70 --junitxml=$REPORTS_DIR/all_tests_$TIMESTAMP.xml; then
    print_success "Análise de cobertura concluída"
    print_status "Relatório HTML disponível em: htmlcov/index.html"
    ((TESTS_PASSED++))
else
    print_warning "Análise de cobertura falhou ou cobertura abaixo do mínimo"
    ((TESTS_FAILED++))
fi

# 6. Verificações de Qualidade
echo
echo "🔍 6. VERIFICAÇÕES DE QUALIDADE"
echo "==============================="

# Flake8
print_status "Executando Flake8..."
if flake8 . --count --statistics --max-line-length=127 --output-file=$REPORTS_DIR/flake8_$TIMESTAMP.txt; then
    print_success "Flake8 passou"
else
    print_warning "Flake8 encontrou problemas"
fi

# Black
print_status "Verificando formatação com Black..."
if black --check --diff . >$REPORTS_DIR/black_$TIMESTAMP.txt; then
    print_success "Código bem formatado"
else
    print_warning "Código precisa de formatação"
fi

# isort
print_status "Verificando imports com isort..."
if isort --check-only --diff . >$REPORTS_DIR/isort_$TIMESTAMP.txt; then
    print_success "Imports bem organizados"
else
    print_warning "Imports precisam de organização"
fi

# 7. Verificações de Segurança
echo
echo "🔒 7. VERIFICAÇÕES DE SEGURANÇA"
echo "==============================="

# Bandit
if command_exists bandit; then
    print_status "Executando Bandit (análise de segurança)..."
    if bandit -r . -f json -o $REPORTS_DIR/bandit_$TIMESTAMP.json; then
        print_success "Bandit concluído"
    else
        print_warning "Bandit encontrou problemas potenciais"
    fi
else
    print_warning "Bandit não instalado"
fi

# Safety
if command_exists safety; then
    print_status "Executando Safety (vulnerabilidades de dependências)..."
    if safety check --json --output $REPORTS_DIR/safety_$TIMESTAMP.json; then
        print_success "Safety concluído"
    else
        print_warning "Safety encontrou vulnerabilidades"
    fi
else
    print_warning "Safety não instalado"
fi

# 8. Testes de Performance (se disponíveis)
echo
echo "⚡ 8. TESTES DE PERFORMANCE"
echo "=========================="

if pytest tests/test_integration.py::TestPerformance -v --benchmark-only --benchmark-json=$REPORTS_DIR/benchmark_$TIMESTAMP.json 2>/dev/null; then
    print_success "Testes de performance concluídos"
else
    print_warning "Testes de performance não disponíveis ou falharam"
fi

# 9. Gerar Relatório Consolidado
echo
echo "📄 9. RELATÓRIO CONSOLIDADO"
echo "=========================="

REPORT_FILE="$REPORTS_DIR/consolidated_report_$TIMESTAMP.md"

cat >$REPORT_FILE <<EOF
# Relatório de Testes - SIA2

**Data/Hora:** $(date)
**Timestamp:** $TIMESTAMP

## Resumo Executivo

- ✅ Testes Passaram: $TESTS_PASSED
- ❌ Testes Falharam: $TESTS_FAILED
- 📊 Taxa de Sucesso: $((TESTS_PASSED * 100 / (TESTS_PASSED + TESTS_FAILED)))%

## Detalhes dos Testes

### 1. Testes Unitários (Modelos)
- Arquivo: \`tests/test_models.py\`
- Relatório: \`models_$TIMESTAMP.xml\`

### 2. Testes de Autenticação
- Arquivo: \`tests/test_auth.py\`
- Relatório: \`auth_$TIMESTAMP.xml\`

### 3. Testes de Rotas Administrativas
- Arquivo: \`tests/test_admin_routes.py\`
- Relatório: \`admin_$TIMESTAMP.xml\`

### 4. Testes de Integração
- Arquivo: \`tests/test_integration.py\`
- Relatório: \`integration_$TIMESTAMP.xml\`

### 5. Cobertura de Código
- Relatório HTML: \`htmlcov/index.html\`
- Relatório XML: \`coverage_$TIMESTAMP.xml\`

## Qualidade de Código

### Linting
- Flake8: \`flake8_$TIMESTAMP.txt\`
- Black: \`black_$TIMESTAMP.txt\`
- isort: \`isort_$TIMESTAMP.txt\`

### Segurança
- Bandit: \`bandit_$TIMESTAMP.json\`
- Safety: \`safety_$TIMESTAMP.json\`

### Performance
- Benchmark: \`benchmark_$TIMESTAMP.json\`

## Próximos Passos

1. Revisar testes que falharam
2. Verificar cobertura de código
3. Resolver problemas de qualidade identificados
4. Atualizar dependências com vulnerabilidades

EOF

print_success "Relatório consolidado gerado: $REPORT_FILE"

# 10. Resumo Final
echo
echo "📋 RESUMO FINAL"
echo "==============="

echo "📊 Estatísticas:"
echo "  • Testes executados: $((TESTS_PASSED + TESTS_FAILED))"
echo "  • Testes passaram: $TESTS_PASSED"
echo "  • Testes falharam: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "🎉 Todos os testes passaram!"
    echo "✅ Pipeline de testes concluído com sucesso"
    exit 0
else
    print_warning "⚠️  Alguns testes falharam"
    echo "📁 Verifique os relatórios em: $REPORTS_DIR"
    echo "🔍 Relatório consolidado: $REPORT_FILE"
    exit 1
fi
