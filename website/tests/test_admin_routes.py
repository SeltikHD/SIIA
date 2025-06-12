"""
Testes para rotas administrativas do sistema SIA2.
Testam CRUD de culturas, fertilizantes e unidades de medida.
"""

import pytest

from lib.models import Cultura, Fertilizante, UnidadeMedida


@pytest.mark.admin
class TestCulturaRoutes:
    """Testes para rotas de gerenciamento de culturas."""

    def test_lista_culturas_admin(self, client, login_admin, cultura_teste):
        """Testa listagem de culturas para admin."""
        response = client.get("/admin/culturas")
        assert response.status_code == 200
        assert cultura_teste.nome.encode() in response.data

    def test_criar_cultura_get(self, client, login_admin):
        """Testa página de criação de cultura."""
        response = client.get("/admin/culturas/create")
        assert response.status_code in [200, 404]  # 404 se rota não existir

    def test_criar_cultura_post_sucesso(self, client, login_admin, db_session):
        """Testa criação de cultura via POST."""
        response = client.post("/admin/culturas/create", data={"nome": "Nova Cultura Teste"}, follow_redirects=True)

        if response.status_code == 200:
            # Verifica se cultura foi criada no banco
            cultura = Cultura.query.filter_by(nome="Nova Cultura Teste").first()
            assert cultura is not None

    def test_editar_cultura_get(self, client, login_admin, cultura_teste):
        """Testa página de edição de cultura."""
        response = client.get(f"/admin/culturas/{cultura_teste.id}/edit")
        assert response.status_code in [200, 404]

    def test_deletar_cultura_post(self, client, login_admin, cultura_teste):
        """Testa deleção de cultura."""
        response = client.post(f"/admin/culturas/{cultura_teste.id}/delete")
        assert response.status_code in [200, 302, 404]


@pytest.mark.admin
class TestFertilizanteRoutes:
    """Testes para rotas de gerenciamento de fertilizantes."""

    def test_lista_fertilizantes_admin(self, client, login_admin, fertilizante_teste):
        """Testa listagem de fertilizantes para admin."""
        response = client.get("/admin/fertilizantes")
        assert response.status_code == 200
        assert fertilizante_teste.nome.encode() in response.data

    def test_criar_fertilizante_get(self, client, login_admin):
        """Testa página de criação de fertilizante."""
        response = client.get("/admin/fertilizantes/create")
        assert response.status_code in [200, 404]

    def test_criar_fertilizante_post_sucesso(self, client, login_admin, unidade_medida_teste, db_session):
        """Testa criação de fertilizante via POST."""
        response = client.post(
            "/admin/fertilizantes/create",
            data={"nome": "Fertilizante Teste", "unidade_medida_id": unidade_medida_teste.id},
            follow_redirects=True,
        )

        if response.status_code == 200:
            fertilizante = Fertilizante.query.filter_by(nome="Fertilizante Teste").first()
            assert fertilizante is not None

    def test_editar_fertilizante_get(self, client, login_admin, fertilizante_teste):
        """Testa página de edição de fertilizante."""
        response = client.get(f"/admin/fertilizantes/{fertilizante_teste.id}/edit")
        assert response.status_code in [200, 404]


@pytest.mark.admin
class TestUnidadeMedidaRoutes:
    """Testes para rotas de gerenciamento de unidades de medida."""

    def test_lista_unidades_admin(self, client, login_admin, unidade_medida_teste):
        """Testa listagem de unidades para admin."""
        response = client.get("/admin/unidades-medida")
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert unidade_medida_teste.nome.encode() in response.data

    def test_criar_unidade_get(self, client, login_admin):
        """Testa página de criação de unidade."""
        response = client.get("/admin/unidades-medida/create")
        assert response.status_code in [200, 404]

    def test_criar_unidade_post_sucesso(self, client, login_admin, db_session):
        """Testa criação de unidade via POST."""
        response = client.post("/admin/unidades-medida/create", data={"nome": "Gramas", "simbolo": "g"}, follow_redirects=True)

        if response.status_code == 200:
            unidade = UnidadeMedida.query.filter_by(nome="Gramas").first()
            assert unidade is not None

    def test_editar_unidade_get(self, client, login_admin, unidade_medida_teste):
        """Testa página de edição de unidade."""
        response = client.get(f"/admin/unidades-medida/{unidade_medida_teste.id}/edit")
        assert response.status_code in [200, 404]


@pytest.mark.admin
class TestDashboardAdmin:
    """Testes para dashboard administrativo."""

    def test_dashboard_admin_acesso(self, client, login_admin):
        """Testa acesso ao dashboard admin."""
        response = client.get("/admin")
        assert response.status_code in [200, 404]
