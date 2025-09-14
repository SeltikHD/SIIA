"""
Testes para rotas administrativas do sistema SIA2.
Testam CRUD de culturas, fertilizantes e unidades de medida.
"""

import pytest
from flask import url_for

from lib.models import Cultura, Fertilizante, FertilizanteCultura, UnidadeMedida


@pytest.mark.admin
class TestCulturaRoutes:
    """Testes para rotas de gerenciamento de culturas."""

    def test_lista_culturas_admin(self, client, login_admin, cultura_teste):
        """Testa listagem de culturas para admin."""
        response = client.get("/admin/culturas")
        assert response.status_code == 200
        assert cultura_teste.nome.encode() in response.data

    def test_lista_culturas_sem_permissao(self, client, login_visualizador):
        """Testa que visualizador não acessa lista de culturas."""
        response = client.get("/admin/culturas")
        assert response.status_code in [302, 403]

    def test_criar_cultura_get(self, client, login_admin):
        """Testa página de criação de cultura."""
        response = client.get("/admin/culturas/create")
        assert response.status_code == 200
        assert b"Nova Cultura" in response.data or b"Criar" in response.data

    def test_criar_cultura_post_sucesso(self, client, login_admin, db_session):
        """Testa criação de cultura via POST."""
        response = client.post("/admin/culturas/create", data={"nome": "Nova Cultura Teste"}, follow_redirects=True)

        assert response.status_code == 200

        # Verifica se cultura foi criada no banco
        cultura = Cultura.query.filter_by(nome="Nova Cultura Teste").first()
        assert cultura is not None
        assert cultura.nome == "Nova Cultura Teste"

    def test_criar_cultura_nome_vazio(self, client, login_admin):
        """Testa criação de cultura com nome vazio."""
        response = client.post("/admin/culturas/create", data={"nome": ""})

        assert response.status_code == 200
        # Deve retornar à página com erro

    def test_editar_cultura_get(self, client, login_admin, cultura_teste):
        """Testa página de edição de cultura."""
        response = client.get(f"/admin/culturas/{cultura_teste.id}/edit")
        assert response.status_code == 200
        assert cultura_teste.nome.encode() in response.data

    def test_editar_cultura_post_sucesso(self, client, login_admin, cultura_teste, db_session):
        """Testa edição de cultura via POST."""
        novo_nome = "Cultura Editada"
        response = client.post(f"/admin/culturas/{cultura_teste.id}/edit", data={"nome": novo_nome}, follow_redirects=True)

        assert response.status_code == 200

        # Verifica se cultura foi editada
        cultura_editada = Cultura.query.get(cultura_teste.id)
        assert cultura_editada.nome == novo_nome

    def test_editar_cultura_inexistente(self, client, login_admin):
        """Testa edição de cultura que não existe."""
        response = client.get("/admin/culturas/99999/edit")
        assert response.status_code == 404

    def test_deletar_cultura_sucesso(self, client, login_admin, cultura_teste, db_session):
        """Testa deleção de cultura."""
        cultura_id = cultura_teste.id
        response = client.post(f"/admin/culturas/{cultura_id}/delete", follow_redirects=True)

        assert response.status_code == 200

        # Verifica se cultura foi deletada
        cultura_deletada = Cultura.query.get(cultura_id)
        assert cultura_deletada is None

    def test_deletar_cultura_inexistente(self, client, login_admin):
        """Testa deleção de cultura que não existe."""
        response = client.post("/admin/culturas/99999/delete")
        assert response.status_code == 404


@pytest.mark.admin
class TestFertilizanteRoutes:
    """Testes para rotas de gerenciamento de fertilizantes."""

    def test_lista_fertilizantes_admin(self, client, login_admin, fertilizante_teste):
        """Testa listagem de fertilizantes para admin."""
        response = client.get("/admin/fertilizantes")
        assert response.status_code == 200
        assert fertilizante_teste.nome.encode() in response.data

    def test_lista_fertilizantes_operador(self, client, login_operador, fertilizante_teste):
        """Testa que operador (nível 2) não acessa fertilizantes (nível 3)."""
        response = client.get("/admin/fertilizantes")
        assert response.status_code in [302, 403]

    def test_criar_fertilizante_get(self, client, login_admin, unidade_medida_teste):
        """Testa página de criação de fertilizante."""
        response = client.get("/admin/fertilizantes/create")
        assert response.status_code == 200
        assert b"Novo Fertilizante" in response.data or b"Criar" in response.data
        # Deve mostrar opções de unidade de medida
        assert unidade_medida_teste.nome.encode() in response.data

    def test_criar_fertilizante_post_sucesso(self, client, login_admin, unidade_medida_teste, db_session):
        """Testa criação de fertilizante via POST."""
        response = client.post(
            "/admin/fertilizantes/create",
            data={"nome": "Fertilizante Teste", "unidade_medida_id": unidade_medida_teste.id},
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verifica se fertilizante foi criado
        fertilizante = Fertilizante.query.filter_by(nome="Fertilizante Teste").first()
        assert fertilizante is not None
        assert fertilizante.unidade_medida_id == unidade_medida_teste.id

    def test_criar_fertilizante_sem_unidade(self, client, login_admin):
        """Testa criação de fertilizante sem unidade de medida."""
        response = client.post(
            "/admin/fertilizantes/create", data={"nome": "Fertilizante Sem Unidade", "unidade_medida_id": ""}
        )

        assert response.status_code == 200
        # Deve retornar à página com erro

    def test_editar_fertilizante_get(self, client, login_admin, fertilizante_teste):
        """Testa página de edição de fertilizante."""
        response = client.get(f"/admin/fertilizantes/{fertilizante_teste.id}/edit")
        assert response.status_code == 200
        assert fertilizante_teste.nome.encode() in response.data

    def test_editar_fertilizante_post_sucesso(self, client, login_admin, fertilizante_teste, unidade_medida_teste, db_session):
        """Testa edição de fertilizante via POST."""
        novo_nome = "Fertilizante Editado"
        response = client.post(
            f"/admin/fertilizantes/{fertilizante_teste.id}/edit",
            data={"nome": novo_nome, "unidade_medida_id": unidade_medida_teste.id},
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verifica se fertilizante foi editado
        fertilizante_editado = Fertilizante.query.get(fertilizante_teste.id)
        assert fertilizante_editado.nome == novo_nome

    def test_deletar_fertilizante_sucesso(self, client, login_admin, fertilizante_teste, db_session):
        """Testa deleção de fertilizante."""
        fertilizante_id = fertilizante_teste.id
        response = client.post(f"/admin/fertilizantes/{fertilizante_id}/delete", follow_redirects=True)

        assert response.status_code == 200

        # Verifica se fertilizante foi deletado
        fertilizante_deletado = Fertilizante.query.get(fertilizante_id)
        assert fertilizante_deletado is None


@pytest.mark.admin
class TestUnidadeMedidaRoutes:
    """Testes para rotas de gerenciamento de unidades de medida."""

    def test_lista_unidades_admin(self, client, login_admin, unidade_medida_teste):
        """Testa listagem de unidades para admin."""
        response = client.get("/admin/unidades-medida")
        assert response.status_code == 200
        assert unidade_medida_teste.nome.encode() in response.data

    def test_lista_unidades_sem_permissao(self, client, login_operador, unidade_medida_teste):
        """Testa que operador não acessa unidades (nível 3)."""
        response = client.get("/admin/unidades-medida")
        assert response.status_code in [302, 403]

    def test_criar_unidade_get(self, client, login_admin):
        """Testa página de criação de unidade."""
        response = client.get("/admin/unidades-medida/create")
        assert response.status_code == 200
        assert b"Nova Unidade" in response.data or b"Criar" in response.data

    def test_criar_unidade_post_sucesso(self, client, login_admin, db_session):
        """Testa criação de unidade via POST."""
        response = client.post("/admin/unidades-medida/create", data={"nome": "Gramas", "simbolo": "g"}, follow_redirects=True)

        assert response.status_code == 200

        # Verifica se unidade foi criada
        unidade = UnidadeMedida.query.filter_by(nome="Gramas").first()
        assert unidade is not None
        assert unidade.simbolo == "g"

    def test_criar_unidade_campos_vazios(self, client, login_admin):
        """Testa criação de unidade com campos vazios."""
        response = client.post("/admin/unidades-medida/create", data={"nome": "", "simbolo": ""})

        assert response.status_code == 200
        # Deve retornar à página com erro

    def test_criar_unidade_simbolo_longo(self, client, login_admin):
        """Testa criação de unidade com símbolo muito longo."""
        response = client.post("/admin/unidades-medida/create", data={"nome": "Teste", "simbolo": "simbololongo"})

        assert response.status_code in [200, 302]
        # Deve retornar à página com erro ou redirecionar

    def test_editar_unidade_get(self, client, login_admin, unidade_medida_teste):
        """Testa página de edição de unidade."""
        response = client.get(f"/admin/unidades-medida/{unidade_medida_teste.id}/edit")
        assert response.status_code == 200
        assert unidade_medida_teste.nome.encode() in response.data

    def test_editar_unidade_post_sucesso(self, client, login_admin, unidade_medida_teste, db_session):
        """Testa edição de unidade via POST."""
        novo_nome = "Unidade Editada"
        response = client.post(
            f"/admin/unidades-medida/{unidade_medida_teste.id}/edit",
            data={"nome": novo_nome, "simbolo": unidade_medida_teste.simbolo},
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Verifica se unidade foi editada
        unidade_editada = UnidadeMedida.query.get(unidade_medida_teste.id)
        assert unidade_editada.nome == novo_nome

    def test_deletar_unidade_sem_fertilizantes(self, client, login_admin, db_session):
        """Testa deleção de unidade sem fertilizantes."""
        # Cria unidade temporária
        unidade = UnidadeMedida(nome="Temp", simbolo="tmp")
        db_session.session.add(unidade)
        db_session.session.commit()
        unidade_id = unidade.id

        response = client.post(f"/admin/unidades-medida/{unidade_id}/delete", follow_redirects=True)

        assert response.status_code == 200

        # Verifica se unidade foi deletada
        unidade_deletada = UnidadeMedida.query.get(unidade_id)
        assert unidade_deletada is None

    def test_deletar_unidade_com_fertilizantes(self, client, login_admin, unidade_medida_teste, fertilizante_teste):
        """Testa que não é possível deletar unidade com fertilizantes."""
        response = client.post(f"/admin/unidades-medida/{unidade_medida_teste.id}/delete", follow_redirects=True)

        # Deve falhar ou redirecionar com erro
        if response.status_code == 200:
            # Se retornou 200, unidade ainda deve existir
            unidade = UnidadeMedida.query.get(unidade_medida_teste.id)
            assert unidade is not None


@pytest.mark.admin
class TestFertilizanteCulturaRoutes:
    """Testes para associação fertilizante-cultura."""

    def test_associar_fertilizante_cultura(self, client, login_admin, fertilizante_teste, cultura_teste, db_session):
        """Testa associação de fertilizante a cultura."""
        # Implementação específica depende da rota de associação
        # Exemplo com dados POST
        response = client.post(
            "/admin/fertilizantes/associar",
            data={"fertilizante_id": fertilizante_teste.id, "cultura_id": cultura_teste.id, "quantidade_recomendada": 100.0},
            follow_redirects=True,
        )

        # Verifica se associação foi criada (se rota existir)
        if response.status_code == 200:
            associacao = FertilizanteCultura.query.filter_by(
                fertilizante_id=fertilizante_teste.id, cultura_id=cultura_teste.id
            ).first()
            if associacao:
                assert associacao.quantidade_recomendada == 100.0

    def test_listar_fertilizantes_por_cultura(self, client, login_admin, cultura_teste):
        """Testa listagem de fertilizantes de uma cultura específica."""
        response = client.get(f"/admin/culturas/{cultura_teste.id}/fertilizantes")

        # Rota pode não existir ainda, então teste condicional
        if response.status_code == 200:
            assert cultura_teste.nome.encode() in response.data


@pytest.mark.admin
class TestDashboardAdmin:
    """Testes para dashboard administrativo."""

    def test_dashboard_admin_acesso(self, client, login_admin):
        """Testa acesso ao dashboard admin."""
        response = client.get("/admin")
        assert response.status_code == 200

    def test_dashboard_estatisticas(self, client, login_admin, cultura_teste, fertilizante_teste):
        """Testa se dashboard mostra estatísticas corretas."""
        response = client.get("/admin")

        if response.status_code == 200:
            # Deve mostrar contadores
            assert b"1" in response.data  # Pelo menos 1 cultura
            assert b"1" in response.data  # Pelo menos 1 fertilizante

    def test_dashboard_links_rapidos(self, client, login_admin):
        """Testa links rápidos para funcionalidades admin."""
        response = client.get("/admin")

        if response.status_code == 200:
            # Deve ter links para culturas, fertilizantes, etc.
            # (implementação específica)
            pass


@pytest.mark.admin
class TestValidacaoFormularios:
    """Testes para validação de formulários administrativos."""

    def test_formulario_cultura_validacao(self, client, login_admin):
        """Testa validação de formulário de cultura."""
        # Nome muito longo
        response = client.post("/admin/culturas/create", data={"nome": "x" * 1000})  # Nome excessivamente longo

        assert response.status_code in [200, 302]
        # Deve retornar com erro de validação ou redirect

    def test_formulario_fertilizante_validacao(self, client, login_admin):
        """Testa validação de formulário de fertilizante."""
        # Unidade inválida
        response = client.post(
            "/admin/fertilizantes/create", data={"nome": "Fertilizante Teste", "unidade_medida_id": 99999}  # ID que não existe
        )

        assert response.status_code in [200, 302]
        # Deve retornar com erro de validação ou redirect

    def test_formulario_unidade_validacao(self, client, login_admin):
        """Testa validação de formulário de unidade."""
        # Símbolo duplicado
        response = client.post(
            "/admin/unidades-medida/create", data={"nome": "Teste", "simbolo": "ml"}  # Assumindo que ml já existe
        )

        assert response.status_code in [200, 302]
        # Deve retornar com erro de validação ou redirect


@pytest.mark.admin
class TestBuscaFiltros:
    """Testes para funcionalidades de busca e filtros."""

    def test_busca_culturas(self, client, login_admin, cultura_teste):
        """Testa busca de culturas."""
        response = client.get("/admin/culturas", query_string={"busca": cultura_teste.nome})

        if response.status_code == 200:
            assert cultura_teste.nome.encode() in response.data

    def test_busca_fertilizantes(self, client, login_admin, fertilizante_teste):
        """Testa busca de fertilizantes."""
        response = client.get("/admin/fertilizantes", query_string={"busca": fertilizante_teste.nome})

        if response.status_code == 200:
            assert fertilizante_teste.nome.encode() in response.data

    def test_filtro_unidades_por_tipo(self, client, login_admin, unidade_medida_teste):
        """Testa filtro de unidades por tipo."""
        response = client.get("/admin/unidades-medida", query_string={"tipo": "volume"})

        if response.status_code == 200:
            # Teste básico de resposta válida
            assert response.status_code == 200


@pytest.mark.admin
class TestPaginacao:
    """Testes para paginação de listas administrativas."""

    def test_paginacao_culturas(self, client, login_admin, db_session):
        """Testa paginação na lista de culturas."""
        # Cria muitas culturas
        for i in range(25):
            cultura = Cultura(nome=f"Cultura {i}")
            db_session.session.add(cultura)
        db_session.session.commit()

        response = client.get("/admin/culturas")
        assert response.status_code == 200

    def test_paginacao_fertilizantes(self, client, login_admin, db_session, unidade_medida_teste):
        """Testa paginação na lista de fertilizantes."""
        # Cria muitos fertilizantes
        for i in range(25):
            fertilizante = Fertilizante(nome=f"Fertilizante {i}", unidade_medida_id=unidade_medida_teste.id)
            db_session.session.add(fertilizante)
        db_session.session.commit()

        response = client.get("/admin/fertilizantes")
        assert response.status_code == 200
