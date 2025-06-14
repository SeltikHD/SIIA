# Makefile para projeto SIA2 - Docker
.PHONY: help setup validate start stop clean logs shell db-init db-clean mobile

# Comando padrão
help:
	@echo "🚀 SIA2 - Sistema de Automação de Estufa"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make setup      - Configuração inicial completa"
	@echo "  make validate   - Validar configuração"
	@echo "  make start      - Iniciar projeto (web + banco)"
	@echo "  make mobile     - Iniciar com app móvel"
	@echo "  make stop       - Parar todos os serviços"
	@echo "  make restart    - Parar e iniciar novamente"
	@echo "  make logs       - Ver logs em tempo real"
	@echo "  make shell      - Shell na aplicação web"
	@echo "  make db-init    - Inicializar banco de dados"
	@echo "  make db-clean   - Limpar dados do banco"
	@echo "  make clean      - Limpeza completa"
	@echo "  make status     - Status dos containers"
	@echo ""
	@echo "📦 INSTALAÇÃO:"
	@echo "  install          - Instala dependências básicas"
	@echo "  install-dev      - Instala dependências de desenvolvimento"
	@echo ""
	@echo "🧪 TESTES:"
	@echo "  test             - Executa todos os testes"
	@echo "  test-unit        - Executa apenas testes unitários"
	@echo "  test-integration - Executa testes de integração"
	@echo "  test-auth        - Executa testes de autenticação"
	@echo "  test-admin       - Executa testes de rotas administrativas"
	@echo "  test-coverage    - Executa testes com cobertura detalhada"
	@echo "  test-fast        - Executa testes rápidos (sem integração)"
	@echo ""
	@echo "🔍 QUALIDADE:"
	@echo "  lint             - Executa verificações de código"
	@echo "  format           - Formata código automaticamente"
	@echo "  security         - Executa verificações de segurança"
	@echo "  check-all        - Executa todas as verificações"
	@echo ""
	@echo "🏃 EXECUÇÃO:"
	@echo "  run-dev          - Executa servidor de desenvolvimento"
	@echo "  setup-db         - Configura banco de dados"
	@echo ""
	@echo "🧹 LIMPEZA:"
	@echo "  clean            - Remove arquivos temporários"
	@echo "  clean-all        - Limpeza completa"

# Setup inicial
setup:
	@echo "🔧 Executando setup inicial..."
	@chmod +x setup.sh db-init.sh db-rm.sh validate.sh
	@./setup.sh

# Validação
validate:
	@echo "🔍 Validando configuração..."
	@chmod +x validate.sh
	@./validate.sh

# Iniciar projeto
start:
	@echo "🚀 Iniciando projeto SIA2..."
	@docker compose up -d
	@echo "✅ Projeto iniciado!"
	@echo "🌐 Acesse: http://localhost:5000"

# Iniciar com móvel
mobile:
	@echo "📱 Iniciando projeto com app móvel..."
	@docker compose --profile mobile up -d
	@echo "✅ Projeto iniciado com app móvel!"
	@echo "🌐 Web: http://localhost:5000"
	@echo "📱 Mobile: make mobile-run"

# Executar app móvel
mobile-run:
	@echo "📱 Executando app móvel..."
	@docker compose exec mobile python main_app.py

# Parar serviços
stop:
	@echo "🛑 Parando serviços..."
	@docker compose down

# Reiniciar
restart: stop start

# Ver logs
logs:
	@echo "📊 Logs em tempo real (Ctrl+C para sair)..."
	@docker compose logs -f

# Shell na aplicação
shell:
	@echo "🐚 Abrindo shell na aplicação web..."
	@docker compose exec web bash

# Shell no banco
db-shell:
	@echo "🗄️ Abrindo shell no PostgreSQL..."
	@docker compose exec postgres psql -U lopinhos -d siia

# Inicializar banco
db-init:
	@echo "🗄️ Inicializando banco de dados..."
	@chmod +x db-init.sh
	@./db-init.sh

# Limpar banco
db-clean:
	@echo "🧹 Limpando dados do banco..."
	@docker compose down -v
	@docker volume rm sia2_postgres_data 2>/dev/null || true

# Status
status:
	@echo "📊 Status dos containers:"
	@docker compose ps
	@echo ""
	@echo "💾 Volumes:"
	@docker compose config --volumes

# Limpeza completa
clean:
	@echo "🧹 Limpeza completa..."
	@chmod +x db-rm.sh
	@./db-rm.sh

# Rebuild
rebuild:
	@echo "🔨 Reconstruindo imagens..."
	@docker compose build --no-cache

# Desenvolvimento
dev:
	@echo "🔧 Modo desenvolvimento..."
	@docker compose -f docker-compose.yml up -d

# Testes
test-web:
	@echo "🧪 Executando testes web..."
	@docker compose exec web python -m pytest

test-mobile:
	@echo "📱 Executando testes móvel..."
	@docker compose exec mobile python test_integration.py

# Backup banco
backup:
	@echo "💾 Fazendo backup do banco..."
	@mkdir -p backups
	@docker compose exec postgres pg_dump -U lopinhos siia > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup salvo em backups/"

# Instalação
install:
	@echo "📦 Instalando dependências básicas..."
	$(PIP) install -r requirements.txt

install-dev:
	@echo "📦 Instalando dependências de desenvolvimento..."
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt

# Testes
test:
	@echo "🧪 Executando todos os testes..."
	$(PYTEST) -v --tb=short

test-unit:
	@echo "🧪 Executando testes unitários..."
	$(PYTEST) tests/test_models.py -v -m unit

test-integration:
	@echo "🧪 Executando testes de integração..."
	$(PYTEST) tests/test_integration.py -v -m integration

test-auth:
	@echo "🧪 Executando testes de autenticação..."
	$(PYTEST) tests/test_auth.py -v -m auth

test-admin:
	@echo "🧪 Executando testes de rotas administrativas..."
	$(PYTEST) tests/test_admin_routes.py -v -m admin

test-coverage:
	@echo "🧪 Executando testes com cobertura..."
	$(PYTEST) --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80
	@echo "📊 Relatório de cobertura gerado em htmlcov/index.html"

test-fast:
	@echo "🧪 Executando testes rápidos..."
	$(PYTEST) -v -m "unit or auth" --tb=short

test-watch:
	@echo "🧪 Executando testes em modo watch..."
	$(PYTEST) -f

# Qualidade de código
lint:
	@echo "🔍 Verificando qualidade do código..."
	@echo "  → Flake8..."
	$(FLAKE8) . --count --statistics --max-line-length=127
	@echo "  → Black (check)..."
	$(BLACK) --check --diff .
	@echo "  → Isort (check)..."
	$(ISORT) --check-only --diff .

format:
	@echo "🎨 Formatando código..."
	@echo "  → Black..."
	$(BLACK) .
	@echo "  → Isort..."
	$(ISORT) .
	@echo "✅ Código formatado!"

security:
	@echo "🔒 Verificando segurança..."
	@echo "  → Bandit..."
	$(BANDIT) -r . -f txt
	@echo "  → Safety..."
	$(SAFETY) check

check-all: lint security
	@echo "✅ Todas as verificações concluídas!"

# Execução
run-dev:
	@echo "🏃 Iniciando servidor de desenvolvimento..."
	$(PYTHON) app.py

setup-db:
	@echo "🗄️ Configurando banco de dados..."
	$(PYTHON) -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Banco de dados configurado!')"

# Limpeza
clean:
	@echo "🧹 Removendo arquivos temporários..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf reports
	@echo "✅ Limpeza concluída!"

clean-all: clean
	@echo "🧹 Limpeza completa..."
	rm -rf dist
	rm -rf build
	rm -rf *.log
	@echo "✅ Limpeza completa concluída!"

# Configurações especiais
.SILENT: help

# Targets para CI/CD
ci-install:
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt

ci-test:
	$(PYTEST) --cov=. --cov-report=xml --cov-fail-under=80 --junitxml=junit.xml

ci-lint:
	$(FLAKE8) . --count --select=E9,F63,F7,F82 --show-source --statistics
	$(BLACK) --check .
	$(ISORT) --check-only .

ci-security:
	$(BANDIT) -r . -f json -o bandit-report.json
	$(SAFETY) check --json --output safety-report.json

# Desenvolvimento
dev-setup: install-dev setup-db
	@echo "🎉 Ambiente de desenvolvimento configurado!"
	@echo "📋 Próximos passos:"
	@echo "  1. Execute 'make run-dev' para iniciar o servidor"
	@echo "  2. Execute 'make test' para executar os testes"
	@echo "  3. Execute 'make help' para ver mais comandos"

# Comandos úteis para desenvolvimento
test-specific:
	@echo "🧪 Execute um teste específico:"
	@echo "Exemplo: pytest tests/test_models.py::TestUsuario::test_criar_usuario -v"

coverage-report:
	@echo "📊 Gerando relatório de cobertura..."
	$(COVERAGE) html
	@echo "Relatório disponível em htmlcov/index.html"

# Comandos para debug
debug-test:
	@echo "🐛 Executando testes em modo debug..."
	$(PYTEST) --pdb -x

debug-models:
	@echo "🐛 Testando apenas modelos..."
	$(PYTEST) tests/test_models.py -v --tb=long

# Performance
benchmark:
	@echo "⚡ Executando testes de performance..."
	$(PYTEST) tests/test_integration.py::TestPerformance -v --benchmark-only

# Utilitários
requirements-update:
	@echo "📦 Atualizando requirements..."
	$(PIP) freeze > requirements.txt

create-migration:
	@echo "🗄️ Comando para criar migração (implementar com Flask-Migrate)"

# Validação completa antes de commit
pre-commit: format lint test-fast
	@echo "✅ Pronto para commit!"

# Validação completa antes de push
pre-push: check-all test-coverage
	@echo "✅ Pronto para push!"
