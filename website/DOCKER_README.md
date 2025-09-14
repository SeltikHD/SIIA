# 🐳 SIIA - Setup Completo com Docker

Sistema de Automação de Estufa com setup Docker completo, incluindo aplicação web Flask e aplicativo móvel Kivy.

## 🚀 Início Rápido

### 1️⃣ Setup Automático (Recomendado)
```bash
git clone https://github.com/SeltikHD/SIIA
cd SIIA/website
chmod +x setup.sh
./setup.sh
```

### 2️⃣ Setup Manual
```bash
# Configurar ambiente
cp .env.example .env
nano .env  # Configure conforme necessário

# Inicializar
make setup
make start
```

## 📋 Pré-requisitos

- **Docker** 20.10+ e **Docker Compose** v2
- **Git** para clonar o repositório
- **4GB RAM** mínimo
- **X11** (Linux) para app móvel

### Instalação Docker (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo systemctl start docker
sudo usermod -aG docker $USER
# Logout/login para aplicar permissões
```

## 🏗️ Arquitetura Docker

### Serviços
- **postgres**: PostgreSQL 15 com dados persistentes
- **tailwind**: Node.js para compilação CSS
- **web**: Aplicação Flask principal
- **mobile**: App móvel Kivy (profile opcional)

### Portas
- **5000**: Aplicação web
- **5432**: PostgreSQL

### Volumes
- **postgres_data**: Dados do banco persistentes
- **Bind mounts**: Código para desenvolvimento

## ⚙️ Configuração

### Arquivo .env obrigatório
```env
# Banco de dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/siia
DB_NAME=siia
DB_USER=usuario
DB_PASSWORD=senha_segura

# Flask
SECRET_KEY=chave_muito_longa_e_aleatoria

# Admin padrão
ADMIN_USERNAME=admin@siia.ifpb.edu.br
ADMIN_PASSWORD=SIIA@AdminPassword

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app

# Site
SITE_URL=http://localhost:5000

# API Trefle (opcional)
TREFLE_API_KEY=sua_chave_api
```

## 🔧 Scripts Disponíveis

| Script | Função |
|--------|--------|
| `./setup.sh` | Setup inicial completo |
| `./validate.sh` | Validar configuração |
| `./db-init.sh` | Inicializar apenas banco |
| `./db-rm.sh` | Limpeza completa |

## 📜 Comandos Make

| Comando | Descrição |
|---------|-----------|
| `make help` | Lista todos os comandos |
| `make setup` | Setup inicial |
| `make validate` | Validar configuração |
| `make start` | Iniciar projeto |
| `make mobile` | Iniciar com app móvel |
| `make stop` | Parar tudo |
| `make logs` | Ver logs |
| `make shell` | Shell na aplicação |
| `make db-init` | Inicializar banco |
| `make clean` | Limpeza completa |

## 🐳 Comandos Docker Compose

### Básicos
```bash
# Iniciar tudo
docker compose up -d

# Incluir app móvel
docker compose --profile mobile up -d

# Parar
docker compose down

# Logs
docker compose logs -f

# Status
docker compose ps
```

### Debug
```bash
# Shell na aplicação
docker compose exec web bash

# Shell no banco
docker compose exec postgres psql -U lopinhos -d siia

# Rebuild
docker compose build --no-cache
```

## 📱 App Móvel

### Via Docker
```bash
# Iniciar com profile móvel
docker compose --profile mobile up -d

# Executar app (precisa X11)
docker compose exec mobile python main_app.py
```

### Local (alternativa)
```bash
cd mobile
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main_app.py
```

### X11 no Linux
```bash
# Permitir conexões X11
xhost +local:docker
export DISPLAY=:0
```

## 🗄️ Banco de Dados

### Acesso direto
```bash
# Via compose
docker compose exec postgres psql -U lopinhos -d siia

# Via cliente local
psql -h localhost -U lopinhos -d siia
```

### Backup/Restore
```bash
# Backup
make backup

# Restore manual
cat backup.sql | docker compose exec -T postgres psql -U lopinhos siia
```

### Reset completo
```bash
make db-clean
make db-init
```

## 🔍 Validação

Execute para verificar se tudo está configurado:
```bash
./validate.sh
```

Ou usando make:
```bash
make validate
```

## 📊 Monitoramento

### Status
```bash
make status
docker compose ps
docker compose top
```

### Logs
```bash
# Todos os serviços
make logs

# Serviço específico
docker compose logs -f web
docker compose logs -f postgres
```

### Recursos
```bash
docker stats
```

## 🧪 Testes

### Web
```bash
make test-web
# ou
docker compose exec web python -m pytest
```

### Mobile
```bash
make test-mobile
# ou
docker compose exec mobile python test_integration.py
```

### Integração manual
```bash
# Teste da API
curl http://localhost:5000/api/mobile/culturas

# Teste com auth
curl -H "Authorization: Bearer TOKEN" http://localhost:5000/api/mobile/dashboard
```

## 🚨 Troubleshooting

### Porta em uso
```bash
# Verificar porta 5000
sudo lsof -i :5000

# Verificar porta 5432
sudo lsof -i :5432

# Mudar porta no docker-compose.yml se necessário
```

### Permissões Docker
```bash
# Adicionar usuário ao grupo
sudo usermod -aG docker $USER
# Logout/login

# Ou usar sudo temporariamente
sudo docker compose up
```

### Erro .env
```bash
# Criar baseado no exemplo
cp .env.example .env

# Gerar SECRET_KEY
python -c "import secrets; print(secrets.token_hex(64))"
```

### App móvel não abre
```bash
# X11 no Linux
xhost +local:docker
export DISPLAY=:0

# Verificar se container está rodando
docker compose ps

# Executar local se necessário
cd mobile && python main_app.py
```

### Banco não conecta
```bash
# Verificar logs
docker compose logs postgres

# Verificar se está rodando
docker compose ps postgres

# Reiniciar banco
docker compose restart postgres
```

## 🔒 Segurança

### Produção
Para produção, altere:

1. **Senhas padrão** no .env
2. **SECRET_KEY** única
3. **ADMIN_PASSWORD** forte
4. **Firewall** portas desnecessárias
5. **SSL/TLS** com proxy reverso

### Exemplo docker-compose.prod.yml
```yaml
version: '3.8'
services:
  web:
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
    restart: unless-stopped
    
  postgres:
    restart: unless-stopped
    environment:
      - POSTGRES_PASSWORD=${STRONG_DB_PASSWORD}
```

## 📚 Estrutura do Projeto

```
SIIA/
├── website/                    # Aplicação web Flask
│   ├── docker-compose.yml     # Configuração Docker
│   ├── Dockerfile.web         # Imagem Flask
│   ├── .env                   # Configurações (criar)
│   ├── setup.sh              # Setup automático
│   ├── validate.sh           # Validação
│   ├── Makefile              # Comandos úteis
│   ├── app.py                # Aplicação principal
│   ├── requirements.txt      # Dependências Python
│   ├── package.json          # Dependências Node.js
│   ├── init.sql              # Schema banco
│   ├── model.sql             # Dados exemplo
│   └── ...
└── mobile/                    # Aplicativo móvel
    ├── Dockerfile.mobile      # Imagem Kivy
    ├── main_app.py           # App principal
    ├── requirements.txt      # Dependências
    └── src/                  # Código fonte
```

## 🎯 Fluxo Completo

1. **Clone** o repositório
2. **Execute** `./setup.sh` 
3. **Configure** .env conforme necessário
4. **Valide** com `./validate.sh`
5. **Inicie** com `make start`
6. **Acesse** http://localhost:5000
7. **Use** app móvel com `make mobile`

## 📞 Suporte

### Logs importantes
```bash
# Aplicação web
docker compose logs -f web

# Banco de dados  
docker compose logs -f postgres

# Sistema completo
docker compose logs -f
```

### Reset completo
```bash
make clean      # Limpa tudo
make setup      # Reconfigura
```

### Arquivos importantes
- `docker-compose.yml`: Configuração dos serviços
- `.env`: Variáveis de ambiente
- `DOCKER.md`: Documentação detalhada
- `mobile/README.md`: Documentação do app móvel

---

🎉 **O projeto SIIA está pronto para uso com Docker!**

Acesse http://localhost:5000 após executar `make start`.
