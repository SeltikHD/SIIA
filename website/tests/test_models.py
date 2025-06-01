"""
Testes unitários para modelos do sistema SIA2.
"""

from datetime import datetime

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
    UnidadeMedida,
    Usuario,
    db,
)


@pytest.mark.unit
class TestGrupo:
    """Testes para modelo Grupo."""

    def test_criar_grupo(self, db_session):
        """Testa criação de grupo."""
        grupo = Grupo(nome="Teste", nivel_acesso=2)
        db_session.session.add(grupo)
        db_session.session.commit()

        assert grupo.id is not None
        assert grupo.nome == "Teste"
        assert grupo.nivel_acesso == 2

    def test_string_representation(self, db_session):
        """Testa representação em string do grupo."""
        grupo = Grupo(nome="Admin", nivel_acesso=3)
        assert str(grupo) == "Admin"


@pytest.mark.unit
class TestUsuario:
    """Testes para modelo Usuario."""

    def test_criar_usuario(self, db_session, grupo_admin):
        """Testa criação de usuário."""
        ph = PasswordHasher()
        usuario = Usuario(nome="João Silva", email="joao@email.com", senha=ph.hash("senha123"), grupo_id=grupo_admin.id)
        db_session.session.add(usuario)
        db_session.session.commit()

        assert usuario.id is not None
        assert usuario.nome == "João Silva"
        assert usuario.email == "joao@email.com"
        assert usuario.grupo_id == grupo_admin.id

    def test_usuario_possui_grupo(self, db_session, usuario_admin, grupo_admin):
        """Testa relacionamento usuário-grupo."""
        assert usuario_admin.grupo == grupo_admin
        assert usuario_admin.grupo.nome == grupo_admin.nome


@pytest.mark.unit
class TestCultura:
    """Testes para modelo Cultura."""

    def test_criar_cultura(self, db_session):
        """Testa criação de cultura."""
        cultura = Cultura(nome="Alface")
        db_session.session.add(cultura)
        db_session.session.commit()

        assert cultura.id is not None
        assert cultura.nome == "Alface"

    def test_string_representation(self, db_session):
        """Testa representação em string da cultura."""
        cultura = Cultura(nome="Tomate")
        assert str(cultura) == "Tomate"


@pytest.mark.unit
class TestUnidadeMedida:
    """Testes para modelo UnidadeMedida."""

    def test_criar_unidade_medida(self, db_session):
        """Testa criação de unidade de medida."""
        unidade = UnidadeMedida(nome="Litros", simbolo="L")
        db_session.session.add(unidade)
        db_session.session.commit()

        assert unidade.id is not None
        assert unidade.nome == "Litros"
        assert unidade.simbolo == "L"

    def test_string_representation(self, db_session):
        """Testa representação em string da unidade."""
        unidade = UnidadeMedida(nome="Gramas", simbolo="g")
        assert str(unidade) == "Gramas (g)"


@pytest.mark.unit
class TestFertilizante:
    """Testes para modelo Fertilizante."""

    def test_criar_fertilizante(self, db_session, unidade_medida_teste):
        """Testa criação de fertilizante."""
        fertilizante = Fertilizante(nome="Ureia", unidade_medida_id=unidade_medida_teste.id)
        db_session.session.add(fertilizante)
        db_session.session.commit()

        assert fertilizante.id is not None
        assert fertilizante.nome == "Ureia"
        assert fertilizante.unidade_medida_id == unidade_medida_teste.id

    def test_fertilizante_possui_unidade(self, db_session, fertilizante_teste, unidade_medida_teste):
        """Testa relacionamento fertilizante-unidade."""
        assert fertilizante_teste.unidade_medida == unidade_medida_teste


@pytest.mark.unit
class TestFertilizanteCultura:
    """Testes para modelo FertilizanteCultura."""

    def test_criar_associacao(self, db_session, fertilizante_teste, cultura_teste):
        """Testa criação de associação fertilizante-cultura."""
        associacao = FertilizanteCultura(
            fertilizante_id=fertilizante_teste.id, cultura_id=cultura_teste.id, quantidade_recomendada=150.0
        )
        db_session.session.add(associacao)
        db_session.session.commit()

        assert associacao.id is not None
        assert associacao.fertilizante_id == fertilizante_teste.id
        assert associacao.cultura_id == cultura_teste.id
        assert associacao.quantidade_recomendada == 150.0


@pytest.mark.unit
class TestSessao:
    """Testes para modelo Sessao."""

    def test_criar_sessao(self, db_session, cultura_teste):
        """Testa criação de sessão."""
        sessao = Sessao(nome="Cultivo Verão 2024", cultura_id=cultura_teste.id)
        db_session.session.add(sessao)
        db_session.session.commit()

        assert sessao.id is not None
        assert sessao.nome == "Cultivo Verão 2024"
        assert sessao.cultura_id == cultura_teste.id

    def test_sessao_possui_cultura(self, db_session, cultura_teste):
        """Testa relacionamento sessão-cultura."""
        sessao = Sessao(nome="Teste", cultura_id=cultura_teste.id)
        db_session.session.add(sessao)
        db_session.session.commit()

        assert sessao.cultura == cultura_teste


@pytest.mark.unit
class TestDadoPeriodico:
    """Testes para modelo DadoPeriodico."""

    def test_criar_dado_periodico(self, db_session, cultura_teste):
        """Testa criação de dado periódico."""
        sessao = Sessao(nome="Teste Dados", cultura_id=cultura_teste.id)
        db_session.session.add(sessao)
        db_session.session.commit()

        dado = DadoPeriodico(
            data_hora=datetime.now(),
            temperatura=25.5,
            umidade_ar=65.0,
            umidade_solo=45.0,
            cultura_id=cultura_teste.id,
            sessao_id=sessao.id,
            exaustor_ligado=False,
        )
        db_session.session.add(dado)
        db_session.session.commit()

        assert dado.id is not None
        assert dado.temperatura == 25.5
        assert dado.umidade_ar == 65.0
        assert dado.umidade_solo == 45.0
        assert dado.cultura_id == cultura_teste.id
        assert dado.sessao_id == sessao.id
        assert dado.exaustor_ligado == False


@pytest.mark.unit
class TestCondicaoIdeal:
    """Testes para modelo CondicaoIdeal."""

    def test_criar_condicao_ideal(self, db_session, cultura_teste):
        """Testa criação de condição ideal."""
        condicao = CondicaoIdeal(
            temperatura_min=18.0,
            temperatura_max=28.0,
            umidade_ar_min=60.0,
            umidade_ar_max=80.0,
            umidade_solo_min=40.0,
            umidade_solo_max=70.0,
            cultura_id=cultura_teste.id,
        )
        db_session.session.add(condicao)
        db_session.session.commit()

        assert condicao.id is not None
        assert condicao.temperatura_min == 18.0
        assert condicao.temperatura_max == 28.0
        assert condicao.cultura_id == cultura_teste.id

    def test_condicao_possui_cultura(self, db_session, cultura_teste):
        """Testa relacionamento condição-cultura."""
        condicao = CondicaoIdeal(
            temperatura_min=20.0,
            temperatura_max=30.0,
            umidade_ar_min=50.0,
            umidade_ar_max=90.0,
            umidade_solo_min=30.0,
            umidade_solo_max=80.0,
            cultura_id=cultura_teste.id,
        )
        db_session.session.add(condicao)
        db_session.session.commit()

        assert condicao.cultura == cultura_teste
