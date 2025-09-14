# SIIA Web (Flask) – Início rápido com Docker

Interface web do Sistema Inteligente de Irrigação Automatizada (SIIA) usando Flask + PostgreSQL.

## Pré‑requisitos

- Windows/Mac: Docker Desktop
- Linux: Docker Engine e Docker Compose

## Subir o servidor (web + banco)

1) Crie o arquivo de ambiente (padrão funciona):

```bash
cp .env.example .env
```

1) Suba os serviços:

```bash
./up.sh                 # Linux/macOS
# ou
docker compose up -d --build
```

1) Acesse:

<http://localhost:5000>

Parar/limpar:

```bash
docker compose down     # parar
./db-rm.sh              # limpeza completa (containers + volumes)
```

## Banco de Dados

- Recriar banco e opcionalmente dados de exemplo:

```bash
./db-init.sh
```

- Console do Postgres:

```bash
make db-shell
```

## Testes

Execute os testes no container web:

```bash
docker compose exec web pytest -q
```

## Estrutura simplificada

- web (Flask): serviço `web` exposto em 5000
- banco (Postgres): serviço `db` com init automático via `init.sql` e `model.sql`

## Variáveis (.env)

Veja `.env.example`. Por padrão, o compose usa:

- DB_NAME=siia
- DB_USER=lopinhos
- DB_PASSWORD=senha123
- DATABASE_URL=postgresql://lopinhos:senha123@db:5432/siia

## Dicas

- Logs: `docker compose logs -f`
- Rebuild: `docker compose build --no-cache`
