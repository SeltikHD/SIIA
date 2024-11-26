from datetime import datetime
from flask import Flask, render_template, request, session, flash, redirect, url_for
from lib.models import db, Sessao, DadoPeriodico, Cultura, SessaoIrrigacao, Usuario
from werkzeug.serving import is_running_from_reloader
from lib.firebase import initialize_firebase
from argon2 import PasswordHasher, exceptions
from firebase_admin import auth
from lib.mqtt import MQTTClient
from dotenv import load_dotenv
import logging
import base64
import os


ph = PasswordHasher()

# * Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

initialize_firebase()

app.secret_key = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db.init_app(app)

# * Logs
import logging

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# * Configuração do MQTT
if not is_running_from_reloader():
    app.config["MQTT_CLIENT"] = MQTTClient()


# * Rotas
@app.route("/")
def index():
    sessoes_info = []

    # Consulta todas as sessões
    sessoes = Sessao.query.all()

    for sessao in sessoes:
        # Último dado periódicos da sessão
        ultimo_dado = (
            DadoPeriodico.query.filter_by(sessao_id=sessao.id)
            .order_by(DadoPeriodico.data_hora.desc())
            .first()
        )

        # Verifica a cultura associada
        cultura = Cultura.query.get(sessao.cultura_id)

        # Verifica se a sessão está sendo irrigada
        irrigacao = (
            SessaoIrrigacao.query.filter_by(sessao_id=sessao.id)
            .order_by(SessaoIrrigacao.data_inicio.desc())
            .first()
        )
        esta_irrigando = irrigacao.status if irrigacao else False

        # Cálculo de tempo de cultivo (considerando a data de início da irrigação como início do cultivo)
        tempo_cultivo = None
        if irrigacao and irrigacao.data_inicio:
            tempo_cultivo = (datetime.now() - irrigacao.data_inicio).days

        # Prepara a imagem em base64
        imagem_base64 = None
        if ultimo_dado and ultimo_dado.imagem:
            imagem_base64 = base64.b64encode(ultimo_dado.imagem).decode("utf-8")

        # Adiciona as informações de cada sessão
        sessoes_info.append(
            {
                "sessao_nome": sessao.nome,
                "cultura_nome": cultura.nome if cultura else "Sem cultura",
                "tempo_cultivo": tempo_cultivo,
                "ocupada": bool(cultura),
                "esta_irrigando": esta_irrigando,
                "temperatura": ultimo_dado.temperatura if ultimo_dado else "N/A",
                "umidade_ar": ultimo_dado.umidade_ar if ultimo_dado else "N/A",
                "umidade_solo": ultimo_dado.umidade_solo if ultimo_dado else "N/A",
                "imagem_base64": imagem_base64,
            }
        )

    return render_template("index.html", sessoes_info=sessoes_info)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        # Busca o usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário existe e a senha está correta
        try:
            if usuario and ph.verify(usuario.senha, senha):
                # Armazena o ID do usuário na sessão
                session["user_id"] = usuario.id
                flash("Login realizado com sucesso", "success")
                return redirect(url_for("index"))
            else:
                flash("Email ou senha inválidos", "error")
        except exceptions.VerifyMismatchError:
            flash("Email ou senha inválidos", "error")

    return render_template("login.html")


@app.route("/google_login", methods=["POST"])
def google_login():
    id_token = request.json.get("idToken")

    try:
        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token["email"]
        nome = decoded_token.get("name")
        photo_url = decoded_token.get("picture")  # Obtém a URL da imagem de perfil

        if not nome:
            nome = email.split("@")[0].capitalize()

        foto = None
        if photo_url:
            import requests
            from io import BytesIO

            response = requests.get(photo_url)
            foto = BytesIO(response.content).getvalue()  # Converte a imagem para bytes

        # Verifique se o usuário já existe
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            usuario = Usuario(
                nome=nome, email=email, foto=foto
            )  # Adiciona a URL da imagem
            db.session.add(usuario)
            db.session.commit()
        elif (
            (nome or foto)
            and usuario
            and (usuario.nome != nome or usuario.foto != foto)
        ):
            # Atualizar informações do usuário
            usuario.nome = nome
            usuario.foto = foto
            db.session.commit()

        session["user_id"] = usuario.id
        return redirect(url_for("index"))  # Redireciona para a página inicial

    except Exception as e:
        print("Erro ao verificar token:", e)
        return {"message": "Falha na autenticação"}, 401


@app.route("/logout")
def logout():
    # Limpa a sessão do usuário
    session.pop("user_id", None)
    flash("Logout realizado com sucesso", "success")
    return redirect(url_for("login"))


# Outras rotas
@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        # Criptografa a senha
        senha_hash = ph.hash(senha)

        # Cria o novo usuário
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash)
        db.session.add(novo_usuario)
        db.session.commit()

        flash("Cadastro realizado com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("registrar.html")


@app.route("/comando/<acao>/<sessao_id>", methods=["POST"])
def enviar_comando(acao, sessao_id):
    """
    Envia um comando manual via MQTT.
    """
    if acao not in ["irrigacao", "ventilacao", "iluminacao"]:
        logging.warning(f"Ação inválida: {acao}")
        return {"success": False, "message": "Ação inválida."}, 400

    comando = request.json.get("comando", "ON")
    topic = f"estufa/{acao}/manual"

    if app.config["MQTT_CLIENT"].status():
        app.config["MQTT_CLIENT"].publish(
            topic,
            {"sessao_id": sessao_id, "comando": comando},
            qos=2 if acao in ["irrigacao", "ventilacao"] else 1,
        )
        logging.info(f"Comando enviado: {comando} para {topic}")
        return {"success": True, "message": "Comando enviado com sucesso."}
    else:
        logging.error("MQTT não está conectado.")
        return {
            "success": False,
            "message": "Erro ao enviar comando: Broker desconectado.",
        }, 500


if __name__ == "__main__":
    app.run(debug=True)
