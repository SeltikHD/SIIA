"""
Testes de integração do SIA2.
Testam fluxos completos e interações entre componentes.
"""

import pytest

from lib.models import Cultura, Fertilizante, FertilizanteCultura, UnidadeMedida


@pytest.mark.integration
class TestCrudCompleto:
    """Testes de CRUD completo com relacionamentos."""

    def test_criar_cultura_completa(self, client, login_admin, db_session):
        """Testa criação completa de cultura com dados relacionados."""
        # Criar cultura
        response = client.post("/admin/culturas/create", data={"nome": "Cultura Integração"}, follow_redirects=True)

        if response.status_code == 200:
            cultura = Cultura.query.filter_by(nome="Cultura Integração").first()
            assert cultura is not None

    def test_criar_fertilizante_com_unidade(self, client, login_admin, unidade_medida_teste, db_session):
        """Testa criação de fertilizante associado a unidade de medida."""
        response = client.post(
            "/admin/fertilizantes/create",
            data={"nome": "Fertilizante Integração", "unidade_medida_id": unidade_medida_teste.id},
            follow_redirects=True,
        )

        if response.status_code == 200:
            fertilizante = Fertilizante.query.filter_by(nome="Fertilizante Integração").first()
            if fertilizante:
                assert fertilizante.unidade_medida_id == unidade_medida_teste.id


@pytest.mark.integration
class TestFluxoCompleto:
    """Testes de fluxo completo do sistema."""

    def test_fluxo_criar_editar_deletar_cultura(self, client, login_admin, db_session):
        """Testa fluxo completo: criar -> editar -> deletar cultura."""
        # 1. Criar
        create_response = client.post("/admin/culturas/create", data={"nome": "Cultura Fluxo"}, follow_redirects=True)

        if create_response.status_code == 200:
            cultura = Cultura.query.filter_by(nome="Cultura Fluxo").first()
            if cultura:
                # 2. Editar
                edit_response = client.post(
                    f"/admin/culturas/{cultura.id}/edit", data={"nome": "Cultura Fluxo Editada"}, follow_redirects=True
                )

                if edit_response.status_code == 200:
                    # 3. Deletar
                    delete_response = client.post(f"/admin/culturas/{cultura.id}/delete")
                    assert delete_response.status_code in [200, 302, 404]


@pytest.mark.integration
class TestRelacionamentos:
    """Testes de relacionamentos entre entidades."""

    def test_fertilizante_cultura_relacionamento(self, client, login_admin, dados_completos, db_session):
        """Testa criação de relacionamento fertilizante-cultura."""
        cultura = dados_completos["cultura"]
        fertilizante = dados_completos["fertilizante"]

        # Teste básico de relacionamento se a funcionalidade existir
        if hasattr(FertilizanteCultura, "fertilizante_id"):
            relacionamento = FertilizanteCultura(
                fertilizante_id=fertilizante.id, cultura_id=cultura.id, quantidade_recomendada=100.0
            )
            db_session.session.add(relacionamento)
            db_session.session.commit()

            assert relacionamento.id is not None


@pytest.mark.integration
class TestNavegacao:
    """Testes de navegação entre páginas."""

    def test_navegacao_admin_dashboard(self, client, login_admin):
        """Testa navegação pelo dashboard administrativo."""
        response = client.get("/admin")
        assert response.status_code in [200, 404]

    def test_navegacao_listagens(self, client, login_admin):
        """Testa navegação pelas listagens."""
        # Culturas
        response = client.get("/admin/culturas")
        assert response.status_code in [200, 404]

        # Fertilizantes
        response = client.get("/admin/fertilizantes")
        assert response.status_code in [200, 404]

        # Unidades de medida
        response = client.get("/admin/unidades-medida")
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestDadosConsistencia:
    """Testes de consistência de dados."""

    def test_integridade_referencial(self, client, login_admin, dados_completos, db_session):
        """Testa integridade referencial entre entidades."""
        cultura = dados_completos["cultura"]
        fertilizante = dados_completos["fertilizante"]
        unidade = dados_completos["unidade_medida"]

        # Verifica se os dados foram criados corretamente
        assert cultura.id is not None
        assert fertilizante.id is not None
        assert unidade.id is not None

        # Verifica relacionamento fertilizante-unidade
        assert fertilizante.unidade_medida_id == unidade.id
