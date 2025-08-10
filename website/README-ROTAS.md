# SIIA Web – Rotas, funcionalidades, fluxo e status

Este documento resume as rotas do website (Flask), principais funcionalidades, fluxo de execução e o estado atual de funcionamento de cada parte.

## Visão geral do fluxo

- App Flask (`app.py`) com SQLAlchemy (`lib/models.py`) e Flask-Login para autenticação/sessão.
- Variáveis via `.env` (carregadas por `python-dotenv`).
- Banco PostgreSQL (em produção/Docker) ou SQLite de fallback (dev sem .env).
- Firebase opcional para login Google (via `firebase_admin`).
- SMTP opcional para recuperação de senha.
- Painel administrativo com controle de acesso por nível de grupo (decorator `admin_required`).

## Variáveis de ambiente (principais)

- `DATABASE_URL` – URL do banco, ex: `postgresql://lopinhos:senha123@db:5432/siia`.
- `SECRET_KEY` – chave do Flask.
- SMTP: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` (recuperação de senha).
- `SITE_URL` – base para links de recuperação.

## Autenticação e usuário (público)

- `GET /` – Página inicial, lista sessões com dados recentes (temperatura, umidade, imagem base64). Requer tabelas `Sessao`, `DadoPeriodico`, `Cultura`.
- `GET|POST /login` – Login com email/senha (Argon2). Usa `Usuario` e `flask_login`.
- `POST /google_login` – Login com Google (Firebase ID Token). Cria/atualiza `Usuario` e faz login.
- `GET /logout` – Logout do usuário autenticado.
- `GET|POST /registrar` – Registro com menor nível de acesso disponível (busca `Grupo` com menor `nivel_acesso`).
- `GET /perfil` – Página de perfil (autenticado).
- `POST /editar_perfil` – Atualiza nome/email e (opcional) foto (PNG/JPG/JPEG, até 2 MB). Retorna JSON.
- `POST /alterar_senha` – Altera senha (verifica senha atual e força mínimo de 6 chars). Retorna JSON.
- `GET|POST /esqueci_senha` – Solicita recuperação e envia email com token (requer SMTP configurado).
- `GET|POST /redefinir_senha/<token>` – Redefine senha a partir de token válido.

## Administração (níveis de acesso)

O decorator `@admin_required(nivel_minimo)` exige que `current_user.grupo.nivel_acesso >= nivel_minimo`.

- Dashboard (Nível 2+)
  - `GET /admin` – Estatísticas e logs recentes.
  - `GET /admin/culturas` – Lista culturas.
  - `GET /admin/culturas/<id>` – Detalhe de cultura (condições e sessões).
  - `GET /admin/sessoes` – Lista sessões.
  - `GET /admin/sessoes/<id>` – Detalhe de sessão (dados periódicos e irrigações).

- Gestão de Culturas (Nível 3+)
  - `GET|POST /admin/culturas/create` – Cria cultura (único por nome).
  - `GET|POST /admin/culturas/<id>/edit` – Edita cultura (valida duplicidade de nome).
  - `POST /admin/culturas/<id>/delete` – Remove cultura (impede se houver sessões).

- Condições Ideais (Nível 3+)
  - `GET /admin/condicoes-ideais` – Lista condições ideais.
  - `GET|POST /admin/condicoes-ideais/create` – Cria condição por cultura com validações de min<max.

- Fertilizantes (Nível 3+)
  - `GET /admin/fertilizantes` – Lista fertilizantes.
  - `GET|POST /admin/fertilizantes/create` – Cria (requer `UnidadeMedida`).
  - `GET|POST /admin/fertilizantes/<id>/edit` – Edita (valida duplicidade).
  - `POST /admin/fertilizantes/<id>/delete` – Remove (impede se associado a culturas).

- Unidades de Medida (Nível 3+)
  - `GET /admin/unidades-medida` – Lista unidades.
  - `GET|POST /admin/unidades-medida/create` – Cria (nome e símbolo únicos).
  - `GET|POST /admin/unidades-medida/<id>/edit` – Edita (valida duplicidade nome/símbolo).
  - `POST /admin/unidades-medida/<id>/delete` – Remove (impede se houver fertilizantes).

- Sessões de Cultivo (Nível 4+)
  - `GET|POST /admin/sessoes/create` – Cria sessão com vínculo a cultura.
  - `GET|POST /admin/sessoes/<id>/edit` – Edita sessão (nome único; troca de cultura).
  - `POST /admin/sessoes/<id>/delete` – Remove sessão e dados relacionados.

- Usuários e Logs (Nível 5+)
  - `GET /admin/usuarios` – Lista usuários e grupos.
  - `GET|POST /admin/usuarios/<id>/edit` – Edita usuário (nome/email/grupo, valida duplicidade email).
  - `POST /admin/usuarios/<id>/delete` – Remove usuário (impede deletar a si mesmo; limpa logs/tentativas).
  - `GET /admin/logs` – Lista paginada de logs.

## API para app móvel

- `POST /api/mobile/login` – Login (email/senha). Cria/atualiza `SessaoUsuario` (token expira em 7 dias).
- `POST /api/mobile/logout` – Logout por token (apaga sessão móvel).
- `GET /api/mobile/dashboard` – Resumo das sessões (dados recentes, status de irrigação, imagem base64). Requer token válido.
- `GET /api/mobile/culturas` – Lista culturas (modelo simples). Requer token válido.
- `GET /api/mobile/usuarios` – Lista usuários (requer token de usuário com nível >=2).
- `POST /api/mobile/register` – Registro (usa grupo padrão de nível 1).
- `GET /api/mobile/perfil` – Dados do usuário logado + estatísticas gerais.

## Modelos (principais)

- Cultura, CondicaoIdeal, Sessao, SessaoIrrigacao, DadoPeriodico, ControleExaustao.
- UnidadeMedida, Fertilizante, FertilizanteCultura, Fertilizacao.
- Grupo, Usuario, SessaoUsuario, Log, TentativaAcesso, Notificacao, NotificacaoUsuario.

## Estado de funcionamento (observado)

- Subida com Docker (web + db): OK.
- Banco (healthcheck): OK.
- Autenticação básica (session + Argon2): Implementada; depende de dados de `Usuario`.
- Login Google (Firebase): Implementado; opcional (inicialização tolera ausência de `firebase.json`).
- Recuperação de senha (SMTP): Requer configurar SMTP. Sem SMTP, rota funciona mas email não será enviado (retorna mensagem de erro).
- Painel Admin: Implementado com níveis 2–5; depende de dados de `Grupo` e `Usuario`.
- API Móvel: Implementada (login/logout/dashboard/culturas/usuarios/register/perfil) e baseada em token de `SessaoUsuario`.
- Testes: Arquivos presentes (unit, auth, admin, integração). Execução não verificada aqui; recomenda-se `docker compose exec web pytest -q`.

## Observações/risco técnico

- Modelo `Log` possui `usuario_id` declarado duas vezes; ideal remover a duplicidade.
- `Usuario.get_id()` retorna `int`, o Flask-Login geralmente trabalha com `str` (funciona, mas pode padronizar).
- `google_login` faz download da foto via `requests`; em ambientes sem rede, pode falhar (tratado, mas observar timeout).

## Templates

- `templates/` com base (`components/base.html`), páginas públicas e administrativas por domínio (culturas, fertilizantes, unidades, sessões, logs, usuários).

---

Atualizado automaticamente para agrupar sob README.md no VS Code (file nesting).
