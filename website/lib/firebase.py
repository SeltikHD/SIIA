import os

import firebase_admin
from firebase_admin import credentials


def initialize_firebase():
    """Inicializa Firebase se o arquivo de credenciais existir; caso contrário, ignora.

    Evita falhas em ambientes de desenvolvimento/CI sem credenciais.
    """
    cred_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "data", "firebase.json"))
    try:
        if not firebase_admin._apps:
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                # Inicializa sem credenciais (uso apenas de features públicas se necessário)
                firebase_admin.initialize_app()
    except Exception:
        # Em dev/test não devemos quebrar a aplicação por falta de Firebase
        pass
