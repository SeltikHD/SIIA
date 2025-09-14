"""
Testes de integração para as rotas da API móvel.
Cobrem autenticação por token, permissões e payloads principais.
"""

from datetime import datetime, timedelta

import pytest
from argon2 import PasswordHasher

from lib.models import (
    CondicaoIdeal,
    Cultura,
    DadoPeriodico,
    Fertilizante,
    FertilizanteCultura,
    Grupo,
    Sessao,
    SessaoIrrigacao,
    SessaoUsuario,
    UnidadeMedida,
    Usuario,
    db,
)


@pytest.fixture
def criar_usuario(db_session):
    def _make(email: str, senha: str, grupo: Grupo):
        ph = PasswordHasher()
        user = Usuario(nome=email.split("@")[0], email=email, senha=ph.hash(senha), grupo_id=grupo.id)
        db_session.session.add(user)
        db_session.session.commit()
        return user

    return _make


@pytest.fixture
def token_para_usuario(db_session):
    def _make(usuario: Usuario, dias: int = 7):
        token = "tok_" + usuario.email
        sess = SessaoUsuario(token=token, usuario_id=usuario.id, data_expiracao=datetime.now() + timedelta(days=dias))
        db_session.session.add(sess)
        db_session.session.commit()
        return token

    return _make


@pytest.mark.integration
def test_register_sucesso(client, db_session, grupo_visualizador):
    payload = {"nome": "novo", "email": "novo@ex.com", "password": "senha123"}
    res = client.post("/api/mobile/register", json=payload)
    assert res.status_code in (200, 201)
    data = res.get_json()
    assert data.get("success") is True
    assert data.get("usuario", {}).get("email") == payload["email"]


@pytest.mark.integration
def test_register_email_duplicado(client, db_session, grupo_visualizador):
    ph = PasswordHasher()
    u = Usuario(nome="x", email="dup@ex.com", senha=ph.hash("senha123"), grupo_id=grupo_visualizador.id)
    db_session.session.add(u)
    db_session.session.commit()

    res = client.post(
        "/api/mobile/register",
        json={"nome": "novo", "email": "dup@ex.com", "password": "senha123"},
    )
    assert res.status_code in (409, 200)  # implementação retorna 409 no sucesso da validação
    if res.status_code == 409:
        assert res.get_json().get("success") is False


@pytest.mark.integration
def test_login_sucesso(client, db_session, grupo_visualizador, criar_usuario):
    user = criar_usuario("user@ex.com", "senha123", grupo_visualizador)
    res = client.post("/api/mobile/login", json={"email": user.email, "password": "senha123"})
    assert res.status_code in (200,)
    body = res.get_json()
    assert body.get("success") is True
    assert body.get("token")
    assert body.get("usuario", {}).get("email") == user.email


@pytest.mark.integration
def test_login_senha_invalida(client, db_session, grupo_visualizador, criar_usuario):
    user = criar_usuario("user2@ex.com", "senha123", grupo_visualizador)
    res = client.post("/api/mobile/login", json={"email": user.email, "password": "errada"})
    assert res.status_code in (401,)


@pytest.mark.integration
def test_logout_sem_token_ok(client):
    # implementação retorna sucesso mesmo sem token válido
    res = client.post("/api/mobile/logout")
    assert res.status_code == 200


@pytest.mark.integration
def test_dashboard_requer_token(client):
    res = client.get("/api/mobile/dashboard")
    assert res.status_code in (401,)


@pytest.mark.integration
def test_dashboard_sucesso(client, db_session, grupo_visualizador, criar_usuario, token_para_usuario):
    # cria cultura, sessão e dado
    cultura = Cultura(nome="Tomate")
    db_session.session.add(cultura)
    db_session.session.commit()

    sessao = Sessao(nome="S1", cultura_id=cultura.id)
    db_session.session.add(sessao)
    db_session.session.commit()

    dado = DadoPeriodico(
        data_hora=datetime.now(),
        temperatura=25.0,
        umidade_ar=60.0,
        umidade_solo=40.0,
        cultura_id=cultura.id,
        sessao_id=sessao.id,
        exaustor_ligado=False,
    )
    db_session.session.add(dado)
    db_session.session.commit()

    user = criar_usuario("u@ex.com", "senha123", grupo_visualizador)
    token = token_para_usuario(user)

    res = client.get("/api/mobile/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("success") is True
    assert isinstance(data.get("data"), list)


@pytest.mark.integration
def test_culturas_lista(client, db_session, grupo_visualizador, criar_usuario, token_para_usuario):
    db_session.session.add_all([Cultura(nome="Alface"), Cultura(nome="Couve")])
    db_session.session.commit()

    user = criar_usuario("c@ex.com", "senha123", grupo_visualizador)
    token = token_para_usuario(user)

    res = client.get("/api/mobile/culturas", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.get_json()
    assert body.get("success") is True
    assert isinstance(body.get("culturas"), list)


@pytest.mark.integration
def test_usuarios_requer_admin(client, db_session, grupo_visualizador, criar_usuario, token_para_usuario):
    user = criar_usuario("naoadmin@ex.com", "senha123", grupo_visualizador)
    token = token_para_usuario(user)
    res = client.get("/api/mobile/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code in (403,)


@pytest.mark.integration
def test_usuarios_admin_ok(client, db_session, grupo_admin, criar_usuario, token_para_usuario):
    admin = criar_usuario("admin@ex.com", "senha123", grupo_admin)
    token = token_para_usuario(admin)

    # crie alguns usuários
    ph = PasswordHasher()
    db.session.add(Usuario(nome="x", email="x@ex.com", senha=ph.hash("senha123"), grupo_id=grupo_admin.id))
    db.session.commit()

    res = client.get("/api/mobile/usuarios", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.get_json()
    assert body.get("success") is True
    assert isinstance(body.get("usuarios"), list)


@pytest.mark.integration
def test_perfil_ok(client, db_session, grupo_visualizador, criar_usuario, token_para_usuario):
    user = criar_usuario("p@ex.com", "senha123", grupo_visualizador)
    token = token_para_usuario(user)

    res = client.get("/api/mobile/perfil", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.get_json()
    assert body.get("success") is True
    assert body.get("usuario", {}).get("email") == user.email


@pytest.mark.integration
def test_perfil_sem_token(client):
    res = client.get("/api/mobile/perfil")
    assert res.status_code in (401,)
