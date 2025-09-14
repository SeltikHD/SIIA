"""
Configuração de fixtures para testes do SIA2.
"""

import os
import tempfile
from datetime import datetime

import pytest
from argon2 import PasswordHasher

# Configure environment before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

from app import app as flask_app


@pytest.fixture(scope="session")
def app():
    """Cria instância da aplicação para testes."""
    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "LOGIN_DISABLED": False,
        }
    )

    with flask_app.app_context():
        from lib.models import db

        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture(scope="function")
def db_session(app):
    """Session de banco para cada teste."""
    with app.app_context():
        # Import models dynamically after app context
        from lib.models import Cultura, Fertilizante, Grupo, UnidadeMedida, Usuario, db

        # Create all tables
        db.create_all()

        yield db

        # Clean up
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner de comandos CLI."""
    return app.test_cli_runner()


# Fixtures de usuários
@pytest.fixture
def grupo_admin(db_session):
    """Grupo administrador."""
    from lib.models import Grupo

    grupo = Grupo(nome="Administrador", nivel_acesso=3)
    db_session.session.add(grupo)
    db_session.session.commit()
    return grupo


@pytest.fixture
def grupo_operador(db_session):
    """Grupo operador."""
    from lib.models import Grupo

    grupo = Grupo(nome="Operador", nivel_acesso=2)
    db_session.session.add(grupo)
    db_session.session.commit()
    return grupo


@pytest.fixture
def grupo_visualizador(db_session):
    """Grupo visualizador."""
    from lib.models import Grupo

    grupo = Grupo(nome="Visualizador", nivel_acesso=1)
    db_session.session.add(grupo)
    db_session.session.commit()
    return grupo


@pytest.fixture
def usuario_admin(db_session, grupo_admin):
    """Usuário administrador."""
    from lib.models import Usuario

    ph = PasswordHasher()
    usuario = Usuario(nome="Admin Teste", email="admin@teste.com", senha=ph.hash("senha123"), grupo_id=grupo_admin.id)
    db_session.session.add(usuario)
    db_session.session.commit()
    return usuario


@pytest.fixture
def usuario_operador(db_session, grupo_operador):
    """Usuário operador."""
    from lib.models import Usuario

    ph = PasswordHasher()
    usuario = Usuario(nome="Operador Teste", email="operador@teste.com", senha=ph.hash("senha123"), grupo_id=grupo_operador.id)
    db_session.session.add(usuario)
    db_session.session.commit()
    return usuario


@pytest.fixture
def usuario_visualizador(db_session, grupo_visualizador):
    """Usuário visualizador."""
    from lib.models import Usuario

    ph = PasswordHasher()
    usuario = Usuario(
        nome="Visualizador Teste", email="visualizador@teste.com", senha=ph.hash("senha123"), grupo_id=grupo_visualizador.id
    )
    db_session.session.add(usuario)
    db_session.session.commit()
    return usuario


# Fixtures de login
@pytest.fixture
def login_admin(client, usuario_admin):
    """Login como administrador."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(usuario_admin.id)
        sess["_fresh"] = True
    return usuario_admin


@pytest.fixture
def login_operador(client, usuario_operador):
    """Login como operador."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(usuario_operador.id)
        sess["_fresh"] = True
    return usuario_operador


@pytest.fixture
def login_visualizador(client, usuario_visualizador):
    """Login como visualizador."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(usuario_visualizador.id)
        sess["_fresh"] = True
    return usuario_visualizador


# Fixtures de dados
@pytest.fixture
def unidade_medida_teste(db_session):
    """Unidade de medida para testes."""
    from lib.models import UnidadeMedida

    unidade = UnidadeMedida(nome="Mililitros", simbolo="ml")
    db_session.session.add(unidade)
    db_session.session.commit()
    return unidade


@pytest.fixture
def cultura_teste(db_session):
    """Cultura para testes."""
    from lib.models import Cultura

    cultura = Cultura(nome="Tomate")
    db_session.session.add(cultura)
    db_session.session.commit()
    return cultura


@pytest.fixture
def fertilizante_teste(db_session, unidade_medida_teste):
    """Fertilizante para testes."""
    from lib.models import Fertilizante

    fertilizante = Fertilizante(nome="NPK 10-10-10", unidade_medida_id=unidade_medida_teste.id)
    db_session.session.add(fertilizante)
    db_session.session.commit()
    return fertilizante


@pytest.fixture
def dados_completos(db_session, cultura_teste, fertilizante_teste, unidade_medida_teste):
    """Conjunto completo de dados para testes de integração."""
    return {"cultura": cultura_teste, "fertilizante": fertilizante_teste, "unidade_medida": unidade_medida_teste}
