import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    # Substitua pelo caminho para seu arquivo JSON de chave privada
    cred = credentials.Certificate("./static/data/firebase.json")
    firebase_admin.initialize_app(cred)
