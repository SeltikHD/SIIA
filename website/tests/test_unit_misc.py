"""
Testes unitários rápidos para funções/utilitários simples do app.
"""

import base64

from app import allowed_file
from lib.models import Usuario


def test_allowed_file_basico():
    assert allowed_file("foto.png") is True
    assert allowed_file("foto.jpg") is True
    assert allowed_file("foto.jpeg") is True
    assert allowed_file("documento.txt") is False
    assert allowed_file("semextensao") is False


def test_usuario_foto_base64():
    # bytes simples "ok"
    u = Usuario(nome="n", email="e@e.com", grupo_id=1)
    u.foto = b"ok"
    s = u.foto_base64
    assert isinstance(s, str)
    assert base64.b64decode(s) == b"ok"
