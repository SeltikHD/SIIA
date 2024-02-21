from flask import Flask, render_template, request, jsonify
from sklearn.linear_model import LinearRegression
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import secrets
import os

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
db = SQLAlchemy(app)

# Definindo os modelos
class GreenhouseData(db.Model):
    __tablename__ = 'dados_periodicos'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)
    temperatura = db.Column(db.Float, nullable=False)
    umidade = db.Column(db.Float, nullable=False)
    path_image = db.Column(db.Text)
    cultura_id = db.Column(db.Integer, db.ForeignKey('cultura.id'), nullable=False)

class Cultura(db.Model):
    __tablename__ = 'cultura'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.Text, nullable=False)
    trefle_id = db.Column(db.Integer, nullable=False)
    condicoes_ideais = db.relationship('CondicoesIdeais', backref='cultura', lazy=True)

class CondicoesIdeais(db.Model):
    __tablename__ = 'condicoes_ideais'
    id = db.Column(db.Integer, primary_key=True)
    temperatura_min = db.Column(db.Float, nullable=False)
    temperatura_max = db.Column(db.Float, nullable=False)
    umidade_min = db.Column(db.Float, nullable=False)
    umidade_max = db.Column(db.Float, nullable=False)
    cultura_id = db.Column(db.Integer, db.ForeignKey('cultura.id'), nullable=False)

class APIKey(db.Model):
    __tablename__ = 'chave_api'
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.Text, unique=True, nullable=False)
    ativo = db.Column(db.Boolean, nullable=False)


class LogAcesso(db.Model):
    __tablename__ = 'log_acesso'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.TIMESTAMP, nullable=False)
    ip = db.Column(db.String(45), nullable=False)
    chave_api_id = db.Column(db.Integer, db.ForeignKey(
        'chave_api.id'), nullable=False)


@app.route('/')
def index():
    # Exemplo de consulta ao banco de dados para obter os dados mais recentes
    latest_data = GreenhouseData.query.order_by(
        GreenhouseData.timestamp.desc()).first()

    # Exemplo de previsão de temperatura usando regressão linear
    temperatures = [data.temperatura for data in GreenhouseData.query.all()]
    humilities = [data.umidade for data in GreenhouseData.query.all()]
    X = [[temp] for temp in temperatures]
    if len(X) == 0:
        predicted_humidity = 0
    else:
        y = humilities
        model = LinearRegression()
        model.fit(X, y)
        predicted_humidity = model.predict([[latest_data.temperatura]])[0]

    # Exemplo de detecção de anomalias (temperatura abaixo de 10 graus)
    anomalies = GreenhouseData.query.filter(
        GreenhouseData.temperatura < 10).all()

    # Exemplo de reconhecimento de imagem usando OpenCV
    # if latest_data.path_image:
    #    img = cv2.imread(latest_data.path_image)
    # Implemente aqui o código para reconhecimento de imagem
    # (por exemplo, detecção de plantas, pragas, ou doenças)

    return render_template('index.html', latest_data=latest_data, predicted_humidity=predicted_humidity, anomalies=anomalies)


# Rota para inserir dados periódicos
@app.route('/api/inserir_dados', methods=['POST'])
def inserir_dados():
    # Verifica se a chave de API foi fornecida no cabeçalho de autenticação
    chave_api = request.headers.get('Authorization')
    api_key = APIKey.query.filter_by(chave=chave_api, ativo=True).first()

    if not bool(api_key):
        return jsonify({'message': 'Chave de API inválida'}), 401

    # Obtém os dados do corpo da solicitação
    dados = request.json
    timestamp = datetime.now()
    temperatura = dados.get('temperatura')
    umidade = dados.get('umidade')
    path_image = dados.get('path_image')
    cultura_id = dados.get('cultura_id')

    # Verifica se os dados foram fornecidos, se são válidos e se a cultura existe
    if not temperatura or not umidade or not cultura_id:
        return jsonify({'message': 'Dados incompletos'}), 400
    elif temperatura < 0 or temperatura > 100 or umidade < 0 or umidade > 100:
        return jsonify({'message': 'Dados inválidos'}), 400
    elif not Cultura.query.get(cultura_id):
        return jsonify({'message': 'Cultura não encontrada'}), 404

    # Salva os dados no banco de dados
    novo_dado = GreenhouseData(timestamp=timestamp, temperatura=temperatura, umidade=umidade, path_image=path_image, cultura_id=cultura_id)
    db.session.add(novo_dado)
    db.session.commit()

    # Registra o acesso no log
    log_acesso = LogAcesso(timestamp=timestamp, ip=request.remote_addr, chave_api_id=api_key.id)
    db.session.add(log_acesso)
    db.session.commit()

    return jsonify({'message': 'Dados inseridos com sucesso'}), 201


# Rota para gerar uma nova chave de API para um cliente existente
@app.route('/api/nova_chave_api', methods=['POST'])
def nova_chave_api():
    # Verifica se a chave de API foi fornecida no cabeçalho de autenticação
    chave_api = request.headers.get('Authorization')
    api_key = APIKey.query.filter_by(chave=chave_api, ativo=True).first()

    if not bool(api_key):
        return jsonify({'message': 'Chave de API inválida'}), 401

    # Gera uma nova chave de API
    nova_chave = secrets.token_hex(16)

    # Salva a nova chave de API no banco de dados
    nova_api_key = APIKey(chave=nova_chave, ativo=True)
    db.session.add(nova_api_key)
    db.session.commit()

    # Registra o acesso no log
    timestamp = datetime.now()
    log_acesso = LogAcesso(timestamp=timestamp, ip=request.remote_addr, chave_api_id=api_key.id)
    db.session.add(log_acesso)
    db.session.commit()

    return jsonify({'nova_chave_api': nova_chave}), 200


if __name__ == '__main__':
    app.run(debug=True)
