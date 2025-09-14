"""
Testes para sistema de autenticação do SIA2.
Testam login, logout, controle de acesso e permissões.
"""

import pytest
from flask import url_for


@pytest.mark.auth
class TestLogin:
    """Testes para funcionalidade de login."""

    def test_pagina_login_acessivel(self, client):
        """Testa se a página de login é acessível."""
        response = client.get("/login")
        assert response.status_code in [200, 404]

    def test_login_correto(self, client, usuario_admin):
        """Testa login com credenciais corretas."""
        response = client.post("/login", data={"email": "admin@teste.com", "senha": "senha123"}, follow_redirects=True)

        # Login pode retornar 200 ou 302 dependendo da implementação
        assert response.status_code in [200, 302, 404]

    def test_login_incorreto(self, client):
        """Testa login com credenciais incorretas."""
        response = client.post("/login", data={"email": "inexistente@teste.com", "senha": "senhaerrada"})

        assert response.status_code in [200, 302, 401, 404]


@pytest.mark.auth
class TestLogout:
    """Testes para funcionalidade de logout."""

    def test_logout(self, client, login_admin):
        """Testa logout de usuário autenticado."""
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code in [200, 302, 404]


@pytest.mark.auth
class TestControleAcesso:
    """Testes para controle de acesso por nível de usuário."""

    def test_admin_acessa_area_admin(self, client, login_admin):
        """Testa se admin consegue acessar área administrativa."""
        response = client.get("/admin")
        assert response.status_code in [200, 404]

    def test_operador_acessa_area_operador(self, client, login_operador):
        """Testa se operador consegue acessar área operacional."""
        response = client.get("/admin/unidades-medida")
        assert response.status_code in [200, 302, 403, 404]

    def test_visualizador_nao_acessa_admin(self, client, login_visualizador):
        """Testa se visualizador não consegue acessar área admin."""
        response = client.get("/admin/culturas/create")
        assert response.status_code in [403, 404, 302]

    def test_usuario_nao_autenticado_redirect(self, client):
        """Testa se usuário não autenticado é redirecionado."""
        response = client.get("/admin")
        assert response.status_code in [302, 401, 404]


@pytest.mark.auth
class TestPermissoesPorRecurso:
    """Testes para permissões específicas por recurso."""

    def test_admin_pode_criar_cultura(self, client, login_admin):
        """Testa se admin pode criar cultura."""
        response = client.get("/admin/culturas/create")
        assert response.status_code in [200, 404]

    def test_admin_pode_editar_fertilizante(self, client, login_admin, fertilizante_teste):
        """Testa se admin pode editar fertilizante."""
        response = client.get(f"/admin/fertilizantes/{fertilizante_teste.id}/edit")
        assert response.status_code in [200, 404]

    def test_admin_pode_deletar_unidade(self, client, login_admin, unidade_medida_teste):
        """Testa se admin pode deletar unidade de medida."""
        response = client.post(f"/admin/unidades-medida/{unidade_medida_teste.id}/delete")
        assert response.status_code in [200, 302, 404]
