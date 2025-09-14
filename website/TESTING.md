# 🧪 Pipeline de Testes - Sistema SIA2

Este documento descreve o sistema completo de testes implementado para o projeto SIA2 (Sistema Inteligente de Automação).

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Estrutura de Testes](#estrutura-de-testes)
- [Configuração](#configuração)
- [Execução](#execução)
- [Tipos de Teste](#tipos-de-teste)
- [Cobertura](#cobertura)
- [CI/CD](#cicd)
- [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

O sistema de testes do SIA2 implementa as melhores práticas para garantir qualidade, segurança e confiabilidade do código. Inclui:

- ✅ **Testes Unitários** - Modelos, funções isoladas
- ✅ **Testes de Integração** - Fluxos completos
- ✅ **Testes de Autenticação** - Login, permissões, segurança
- ✅ **Testes de Rotas** - APIs e endpoints administrativos
- ✅ **Análise de Cobertura** - Mínimo 80% de cobertura
- ✅ **Verificações de Qualidade** - Linting, formatação
- ✅ **Verificações de Segurança** - Vulnerabilidades, código inseguro
- ✅ **CI/CD Pipeline** - Automação completa

## 📁 Estrutura de Testes

```
tests/
├── conftest.py              # Configurações e fixtures globais
├── test_models.py           # Testes unitários dos modelos
├── test_auth.py             # Testes de autenticação
├── test_admin_routes.py     # Testes de rotas administrativas
├── test_integration.py      # Testes de integração
└── fixtures/                # Fixtures e dados de teste
```

### Arquivos de Configuração

```
├── conftest.py              # Fixtures pytest principais
├── pytest.ini              # Configuração do pytest
├── requirements-test.txt    # Dependências de teste
├── .pre-commit-config.yaml  # Hooks de pre-commit
├── .github/workflows/       # CI/CD GitHub Actions
├── Makefile                 # Comandos facilitados
└── run_tests.sh            # Script completo de testes
```

## ⚙️ Configuração

### 1. Instalar Dependências

```bash
# Dependências básicas
pip install -r requirements.txt

# Dependências de teste
pip install -r requirements-test.txt

# Ou usar o Makefile
make install-dev
```

### 2. Configurar Pre-commit (Opcional)

```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks
pre-commit install

# Executar em todos os arquivos
pre-commit run --all-files
```

### 3. Configurar Banco de Dados de Teste

```bash
# Usar o Makefile
make setup-db

# Ou manualmente
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## 🚀 Execução

### Comandos Rápidos (Makefile)

```bash
# Todos os testes
make test

# Testes rápidos (unitários + auth)
make test-fast

# Testes específicos
make test-unit           # Apenas unitários
make test-integration    # Apenas integração
make test-auth          # Apenas autenticação
make test-admin         # Apenas rotas admin

# Com cobertura
make test-coverage

# Verificações de qualidade
make lint               # Linting
make format            # Formatação automática
make security          # Verificações de segurança
make check-all         # Todas as verificações
```

### Comandos Pytest Diretos

```bash
# Todos os testes
pytest

# Testes com cobertura
pytest --cov=. --cov-report=html

# Testes específicos por marcador
pytest -m unit           # Apenas unitários
pytest -m integration   # Apenas integração
pytest -m auth          # Apenas autenticação
pytest -m admin         # Apenas admin

# Teste específico
pytest tests/test_models.py::TestUsuario::test_criar_usuario -v

# Testes com debug
pytest --pdb -x
```

### Script Completo

```bash
# Execução completa com relatórios
./run_tests.sh

# Permissões (se necessário)
chmod +x run_tests.sh
```

## 🔬 Tipos de Teste

### 1. Testes Unitários (`test_models.py`)

Testam modelos de dados isoladamente:

```python
@pytest.mark.unit
class TestUsuario:
    def test_criar_usuario(self, db_session, grupo_admin):
        # Testa criação de usuário
        
    def test_usuario_grupo_relationship(self, db_session, grupo_operador):
        # Testa relacionamentos
```

**Foco:** Modelos, validações, relacionamentos

### 2. Testes de Autenticação (`test_auth.py`)

Testam sistema de login e permissões:

```python
@pytest.mark.auth
class TestLogin:
    def test_login_sucesso(self, client, usuario_admin):
        # Testa login válido
        
    def test_controle_acesso(self, client, login_visualizador):
        # Testa níveis de acesso
```

**Foco:** Login, logout, permissões, segurança

### 3. Testes de Rotas Admin (`test_admin_routes.py`)

Testam CRUD de entidades administrativas:

```python
@pytest.mark.admin
class TestCulturaRoutes:
    def test_criar_cultura_post_sucesso(self, client, login_admin):
        # Testa criação via formulário
        
    def test_editar_cultura_sem_permissao(self, client, login_operador):
        # Testa controle de acesso
```

**Foco:** CRUD culturas, fertilizantes, unidades

### 4. Testes de Integração (`test_integration.py`)

Testam fluxos completos do sistema:

```python
@pytest.mark.integration
class TestFluxoCompletoCultura:
    def test_ciclo_vida_cultura_completo(self, client, login_admin):
        # Testa criação → uso → edição → deleção
        
class TestFluxoMonitoramento:
    def test_fluxo_coleta_dados_mqtt(self, mock_mqtt, cultura_teste):
        # Testa coleta de dados de sensores
```

**Foco:** Fluxos end-to-end, integrações, performance

## 📊 Cobertura

### Configuração

- **Meta mínima:** 80% de cobertura
- **Falha CI/CD:** Se cobertura < 80%
- **Relatórios:** HTML + XML + Terminal

### Visualizar Relatórios

```bash
# Gerar relatório
make test-coverage

# Abrir no navegador
open htmlcov/index.html

# Via pytest direto
pytest --cov=. --cov-report=html
```

### Exclusões de Cobertura

Arquivos/linhas excluídos da análise:

- Testes próprios
- Migrações de banco
- Configurações de desenvolvimento
- Código de terceiros

## 🔄 CI/CD

### GitHub Actions

Pipeline automático em `.github/workflows/ci-cd.yml`:

```yaml
# Triggers
- Push para main/develop
- Pull requests
- Múltiplas versões Python (3.9, 3.10, 3.11)

# Jobs
1. test       - Executa todos os testes
2. security   - Verificações de segurança
3. quality    - Análise de qualidade
4. build      - Build do projeto
5. deploy     - Deploy (staging/production)
```

### Status Badges

Adicionar ao README principal:

```markdown
![Tests](https://github.com/usuario/sia2/workflows/Tests/badge.svg)
![Coverage](https://codecov.io/gh/usuario/sia2/branch/main/graph/badge.svg)
![Security](https://img.shields.io/badge/security-bandit-green)
```

## 🧩 Fixtures e Mocks

### Fixtures Principais (`conftest.py`)

```python
# Aplicação e banco
@pytest.fixture
def app():           # Instância Flask configurada para testes
def client(app):     # Cliente HTTP para requisições
def db_session(app): # Sessão de banco limpa

# Usuários e grupos
@pytest.fixture
def grupo_admin():        # Grupo nível 3
def usuario_admin():      # Usuário administrador
def login_admin():        # Login automático admin

# Dados de teste
@pytest.fixture
def cultura_teste():      # Cultura para testes
def fertilizante_teste(): # Fertilizante para testes
def dados_completos():    # Dataset completo
```

### Mocks Disponíveis

```python
# Mocks externos
@pytest.fixture
def mock_mqtt():          # Cliente MQTT
def mock_email():         # Sistema de email
def mock_firebase():      # Firebase Auth

# Mocks de tempo
@pytest.fixture
def mock_datetime():      # Datetime fixo (freezegun)
```

## 🛠️ Comandos Úteis

### Desenvolvimento

```bash
# Ambiente completo
make dev-setup

# Teste específico com output detalhado
pytest tests/test_models.py::TestCultura -v -s

# Teste com breakpoint
pytest tests/test_auth.py::TestLogin::test_login_sucesso --pdb

# Executar apenas testes que falharam
pytest --lf

# Executar testes em paralelo
pytest -n auto
```

### Debug

```bash
# Modo debug
make debug-test

# Verbose máximo
pytest -vvv --tb=long

# Com print statements
pytest -s

# Parar no primeiro erro
pytest -x
```

### Performance

```bash
# Benchmarks
make benchmark

# Testes lentos
pytest --durations=10

# Profile de testes
pytest --profile
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Erro de Banco de Dados

```bash
# Recriar banco
make clean
make setup-db

# Verificar configuração
python -c "from app import app, db; print(app.config['SQLALCHEMY_DATABASE_URI'])"
```

#### 2. Imports Não Encontrados

```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstalar dependências
pip install -r requirements-test.txt
```

#### 3. Testes Lentos

```bash
# Executar apenas testes rápidos
pytest -m "not slow"

# Pular testes de integração
pytest -m "not integration"

# Parallelização
pytest -n 4
```

#### 4. Falhas de Cobertura

```bash
# Ver linhas não cobertas
pytest --cov=. --cov-report=term-missing

# Reduzir limite temporariamente
pytest --cov-fail-under=70
```

#### 5. Problemas com Fixtures

```bash
# Debug fixtures
pytest --fixtures

# Verificar escopo
pytest --setup-show
```

### Logs e Debug

```bash
# Habilitar logs detalhados
pytest --log-level=DEBUG

# Capturar stdout
pytest --capture=no

# Salvar output
pytest > test_output.log 2>&1
```

## 📝 Boas Práticas

### Escrevendo Testes

1. **Nomenclatura clara:** `test_funcionalidade_situacao_resultado`
2. **Arrange-Act-Assert:** Preparar → Executar → Verificar
3. **Testes independentes:** Cada teste deve funcionar isoladamente
4. **Dados de teste:** Usar fixtures, não dados hardcoded
5. **Assertions específicas:** Testar comportamentos específicos

### Organização

1. **Marcadores:** Usar `@pytest.mark.unit`, `@pytest.mark.integration`
2. **Classes:** Agrupar testes relacionados
3. **Fixtures:** Reutilizar configurações comuns
4. **Mocks:** Isolar dependências externas

### Performance

1. **Testes rápidos primeiro:** Unitários antes de integração
2. **Paralelização:** Usar `pytest-xdist` quando apropriado
3. **Setup/Teardown eficiente:** Minimizar criação/destruição
4. **Base de dados:** Usar transações com rollback

## 🔗 Links Úteis

- [Documentação Pytest](https://docs.pytest.org/)
- [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Pre-commit](https://pre-commit.com/)
- [GitHub Actions](https://docs.github.com/en/actions)

## 🤝 Contribuindo

1. **Novos testes:** Sempre adicionar testes para novas funcionalidades
2. **Cobertura:** Manter cobertura acima de 80%
3. **Qualidade:** Executar `make check-all` antes de commit
4. **Documentação:** Atualizar este README conforme necessário

---

**🎯 Meta:** 100% dos commits devem passar em todos os testes!

**📞 Suporte:** Para dúvidas sobre testes, consulte a equipe de desenvolvimento.
