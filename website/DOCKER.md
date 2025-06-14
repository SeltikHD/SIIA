# SIA2 - Setup com Docker

Este guia explica como configurar e executar o projeto SIA2 usando Docker.

## 🚀 Início Rápido

### 1. Setup Automático
```bash
chmod +x setup.sh
./setup.sh
```

### 2. Setup Manual

#### Configurar ambiente:
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações necessárias
nano .env
```

#### Inicializar banco:
```bash
chmod +x db-init.sh
./db-init.sh
```

#### Iniciar projeto:
```bash
# Apenas web + banco
docker compose up

# Incluindo app móvel
docker compose --profile mobile up
```

## 📋 Pré-requisitos

- **Docker** e **Docker Compose**
- **Git** (para clonar o projeto)
- **X11** (para app móvel no Linux)

### Instalação Docker (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
# Fazer logout/login para aplicar permissões
```

## 🔧 Configuração

### Arquivo .env obrigatório:
```env
# Banco de dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/siia
DB_NAME=siia
DB_USER=usuario  
DB_PASSWORD=senha

# Flask
SECRET_KEY=sua_chave_secreta_muito_longa

# Admin
ADMIN_USERNAME=admin@siia.ifpb.edu.br
ADMIN_PASSWORD=SIIA@AdminPassword

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_app

# Site
SITE_URL=http://localhost:5000
```

## 🐳 Serviços Docker

### Serviços incluídos:
- **postgres**: Banco PostgreSQL 15
- **tailwind**: Compilação CSS (Node.js)
- **web**: Aplicação Flask principal
- **mobile**: App móvel Kivy (profile opcional)

### Portas expostas:
- **5000**: Aplicação web Flask
- **5432**: PostgreSQL

## 📜 Scripts Disponíveis

### ./setup.sh
Setup inicial completo com configuração interativa do .env

### ./db-init.sh  
Inicializa banco PostgreSQL com Docker Compose

### ./db-rm.sh
Remove containers, volumes e dados do projeto

## 🔄 Comandos Docker Compose

### Básicos:
```bash
# Iniciar tudo
docker compose up

# Iniciar em background
docker compose up -d

# Incluir app móvel
docker compose --profile mobile up

# Parar tudo
docker compose down

# Parar e remover volumes
docker compose down -v
```

### Logs e debug:
```bash
# Ver logs de todos os serviços
docker compose logs -f

# Logs de um serviço específico
docker compose logs -f web

# Executar comando em container
docker compose exec web bash
docker compose exec postgres psql -U lopinhos -d siia
```

### Rebuild:
```bash
# Reconstruir imagens
docker compose build

# Reconstruir e iniciar
docker compose up --build
```

## 📱 App Móvel

### Executar app móvel:
```bash
# Iniciar com profile mobile
docker compose --profile mobile up -d

# Executar app (precisa de X11)
docker compose exec mobile python main_app.py

# No host (se preferir)
cd mobile
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main_app.py
```

### X11 no Linux:
```bash
# Permitir conexões X11
xhost +local:docker

# Ou configurar DISPLAY
export DISPLAY=:0
```

## 🗄️ Banco de Dados

### Conectar diretamente:
```bash
# Via docker compose
docker compose exec postgres psql -U lopinhos -d siia

# Via cliente local (se tiver psql)
psql -h localhost -U lopinhos -d siia
```

### Backup e restore:
```bash
# Backup
docker compose exec postgres pg_dump -U lopinhos siia > backup.sql

# Restore
docker compose exec -T postgres psql -U lopinhos siia < backup.sql
```

## 🔧 Desenvolvimento

### Hot reload:
O volume binding permite edição em tempo real:
- **Web**: Código Python recarrega automaticamente
- **CSS**: Tailwind recompila com --watch
- **Mobile**: Reiniciar container após mudanças

### Debug Flask:
```bash
# Ver logs detalhados
docker compose logs -f web

# Executar shell no container
docker compose exec web bash

# Variáveis de ambiente de debug já configuradas
FLASK_ENV=development
FLASK_DEBUG=1
```

## 🧹 Limpeza

### Limpeza básica:
```bash
./db-rm.sh
```

### Limpeza completa Docker:
```bash
docker system prune -a
docker volume prune
```

## ⚠️ Troubleshooting

### Problema: "Port already in use"
```bash
# Verificar o que usa a porta
sudo lsof -i :5000
sudo lsof -i :5432

# Parar processos ou mudar porta no docker-compose.yml
```

### Problema: "Permission denied" 
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
# Fazer logout/login

# Ou usar sudo
sudo docker compose up
```

### Problema: ".env not found"
```bash
# Criar .env baseado no exemplo
cp .env.example .env
# Editar configurações necessárias
```

### Problema: App móvel não abre
```bash
# X11 no Linux
xhost +local:docker
export DISPLAY=:0

# Executar no host se não funcionar no container
cd mobile && python main_app.py
```

## 📊 Monitoramento

### Status dos serviços:
```bash
docker compose ps
docker compose top
```

### Logs em tempo real:
```bash
# Todos os serviços
docker compose logs -f

# Apenas web
docker compose logs -f web

# Apenas banco
docker compose logs -f postgres
```

### Métricas de uso:
```bash
docker stats
```

## 🚀 Produção

Para ambiente de produção, considere:

1. **Usar imagens específicas de versão**
2. **Configurar secrets adequadamente** 
3. **Usar proxy reverso (nginx)**
4. **Configurar backups automáticos**
5. **Monitoring e alertas**
6. **SSL/TLS**

Exemplo de override para produção:
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
    restart: unless-stopped
  
  postgres:
    restart: unless-stopped
```

Execute com:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
