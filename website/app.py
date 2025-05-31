from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from lib.models import db, Sessao, DadoPeriodico, Cultura, SessaoIrrigacao, Usuario
from werkzeug.serving import is_running_from_reloader
from werkzeug.utils import secure_filename
from lib.firebase import initialize_firebase
from argon2 import PasswordHasher, exceptions
from firebase_admin import auth
from lib.mqtt import MQTTClient
from dotenv import load_dotenv
import logging
import base64
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ph = PasswordHasher()

# * Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

initialize_firebase()

app.secret_key = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar esta página'


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(user_id)


@app.route('/')
def index():
    sessoes_info = []

    # Consulta todas as sessões
    sessoes = Sessao.query.all()

    for sessao in sessoes:
        # Último dado periódicos da sessão
        ultimo_dado = DadoPeriodico.query.filter_by(
            sessao_id=sessao.id).order_by(DadoPeriodico.data_hora.desc()).first()

        # Verifica a cultura associada
        cultura = Cultura.query.get(sessao.cultura_id)

        # Verifica se a sessão está sendo irrigada
        irrigacao = SessaoIrrigacao.query.filter_by(sessao_id=sessao.id).order_by(
            SessaoIrrigacao.data_inicio.desc()).first()
        esta_irrigando = irrigacao.status if irrigacao else False

        # Cálculo de tempo de cultivo (considerando a data de início da irrigação como início do cultivo)
        tempo_cultivo = None
        if irrigacao and irrigacao.data_inicio:
            tempo_cultivo = (datetime.now() - irrigacao.data_inicio).days

        # Prepara a imagem em base64
        imagem_base64 = None
        if ultimo_dado and ultimo_dado.imagem:
            imagem_base64 = base64.b64encode(
                ultimo_dado.imagem).decode('utf-8')

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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form['email']
            senha = request.form['password']
            lembrar = request.form.get('remember')
        except KeyError:
            flash('Email e senha são obrigatórios', 'error')
            return redirect(url_for('login'))

        # Busca o usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário existe e a senha está correta
        try:
            if usuario:
                if usuario.senha:
                    if ph.verify(usuario.senha, senha):
                        login_user(usuario, remember=lembrar)
                        flash('Login realizado com sucesso', 'success')
                        return redirect(url_for('index'))
                    else:
                        flash('Email ou senha inválidos', 'error')
                else:
                    flash(
                        'Esse usuário não possui senha cadastrada, tente fazer login com Google', 'error')
            else:
                flash('Usuário não cadastrado', 'error')
        except exceptions.VerifyMismatchError:
            flash("Email ou senha inválidos", "error")

    return render_template("login.html")


@app.route('/google_login', methods=['POST'])
def google_login():
    id_token = request.json.get("idToken")

    try:
        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token['email']
        nome = decoded_token.get('name')
        # Obtém a URL da imagem de perfil
        photo_url = decoded_token.get('picture')

        if not nome:
            nome = email.split("@")[0].capitalize()

        foto = None
        if photo_url:
            import requests
            from io import BytesIO

            response = requests.get(photo_url)
            # Converte a imagem para bytes
            foto = BytesIO(response.content).getvalue()

        # Verifique se o usuário já existe
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            # Adiciona a URL da imagem
            usuario = Usuario(nome=nome, email=email, foto=foto)
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

        login_user(usuario)

        return redirect(url_for('index'))  # Redireciona para a página inicial

    except Exception as e:
        print("Erro ao verificar token:", e)
        return {"message": "Falha na autenticação"}, 401


@app.route('/logout')
@login_required
def logout():
    # Limpa a sessão do usuário
    logout_user()
    flash('Logout realizado com sucesso', 'success')
    return redirect(url_for('index'))


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == "POST":
        nome = request.form["fullname"]
        email = request.form["email"]
        senha = request.form["password"]
        confirmar = request.form.get("confirm-password")

        # Verifica se as senhas coincidem
        if senha != confirmar:
            flash("As senhas não coincidem.", "error")
            return render_template("registrar.html")

        # Verifica se já existe usuário com o mesmo email
        if Usuario.query.filter_by(email=email).first():
            flash("Já existe um usuário cadastrado com este email.", "error")
            return render_template("registrar.html")

        # Criptografa a senha
        senha_hash = ph.hash(senha)

        # Cria o novo usuário
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash)
        db.session.add(novo_usuario)
        db.session.commit()

        login_user(novo_usuario)
        flash("Cadastro realizado com sucesso! Você já está logado.", "success")
        return redirect(url_for("index"))

    return render_template("registrar.html")


@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html')


@app.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    try:
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()

        if not nome or not email:
            return jsonify({'success': False, 'message': 'Nome e email são obrigatórios'})

        # Verifica se o email já está em uso por outro usuário
        if email != current_user.email:
            usuario_existente = Usuario.query.filter_by(email=email).first()
            if usuario_existente:
                return jsonify({'success': False, 'message': 'Este email já está sendo usado por outro usuário'})

        # Atualiza os dados do usuário
        current_user.nome = nome
        current_user.email = email

        # Processa a foto se foi enviada
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto.filename != '':
                if foto and allowed_file(foto.filename):
                    # Limita o tamanho da imagem (2MB)
                    foto.seek(0, 2)  # Vai para o final do arquivo
                    size = foto.tell()
                    foto.seek(0)  # Volta para o início

                    if size > 2 * 1024 * 1024:  # 2MB
                        return jsonify({'success': False, 'message': 'A imagem deve ter no máximo 2MB'})

                    current_user.foto = foto.read()
                else:
                    return jsonify({'success': False, 'message': 'Formato de imagem inválido. Use JPG, JPEG ou PNG'})

        db.session.commit()
        return jsonify({'success': True, 'message': 'Perfil atualizado com sucesso!'})

    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})


@app.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    try:
        senha_atual = request.form.get('senha_atual', '').strip()
        nova_senha = request.form.get('nova_senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()

        if not senha_atual or not nova_senha or not confirmar_senha:
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'})

        if nova_senha != confirmar_senha:
            return jsonify({'success': False, 'message': 'As senhas não coincidem'})

        if len(nova_senha) < 6:
            return jsonify({'success': False, 'message': 'A nova senha deve ter pelo menos 6 caracteres'})

        # Verifica se o usuário tem senha (pode ter sido criado via Google)
        if not current_user.senha:
            return jsonify({'success': False, 'message': 'Este usuário não possui senha. Entre em contato com o administrador'})

        # Verifica a senha atual - CORRIGIDO: ordem dos parâmetros
        try:
            ph.verify(current_user.senha, senha_atual)
        except exceptions.VerifyMismatchError:
            return jsonify({'success': False, 'message': 'Senha atual incorreta'})
        except exceptions.VerificationError:
            return jsonify({'success': False, 'message': 'Erro na verificação da senha'})

        # Atualiza a senha
        current_user.senha = ph.hash(nova_senha)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Senha alterada com sucesso!'})

    except Exception as e:
        db.session.rollback()
        # Para debug - removar em produção
        print(f"Erro na alteração de senha: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})


@app.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash('Email é obrigatório', 'error')
            return render_template('esqueci_senha.html')

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            # Gera token de recuperação
            token = secrets.token_urlsafe(32)
            usuario.token_recuperacao = token
            db.session.commit()
            
            # Envia email (simulado - em produção usar serviço real)
            try:
                enviar_email_recuperacao(email, token)
                flash('Instruções de recuperação foram enviadas para seu email', 'success')
            except Exception:
                flash('Erro ao enviar email. Tente novamente mais tarde', 'error')
        else:
            # Por segurança, não revela se o email existe ou não
            flash('Se o email estiver cadastrado, você receberá as instruções de recuperação', 'success')
        
        return redirect(url_for('login'))
    
    return render_template('esqueci_senha.html')


@app.route('/redefinir_senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    usuario = Usuario.query.filter_by(token_recuperacao=token).first()

    if not usuario:
        flash('Token inválido ou expirado', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()

        if not nova_senha or not confirmar_senha:
            flash('Todos os campos são obrigatórios', 'error')
            return render_template('redefinir_senha.html', token=token)

        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem', 'error')
            return render_template('redefinir_senha.html', token=token)

        if len(nova_senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres', 'error')
            return render_template('redefinir_senha.html', token=token)

        # Atualiza a senha e remove o token
        usuario.senha = ph.hash(nova_senha)
        usuario.token_recuperacao = None
        db.session.commit()

        flash('Senha redefinida com sucesso! Faça login com sua nova senha', 'success')
        return redirect(url_for('login'))
    
    return render_template('redefinir_senha.html', token=token)


def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def enviar_email_recuperacao(email, token):
    """Envia email real de recuperação de senha via SMTP"""
    try:
        # Configurações SMTP a partir das variáveis de ambiente
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')

        if not all([smtp_server, smtp_username, smtp_password]):
            print("Configurações SMTP incompletas")
            raise ValueError("Configurações SMTP não encontradas")

        # Cria a mensagem de email
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = 'Recuperação de Senha - SIIA'

        # Corpo do email em HTML
        link_recuperacao = f"http://localhost:5000/redefinir_senha/{token}"
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Recuperação de Senha</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Recuperação de Senha - SIIA</h2>

                <p>Olá,</p>

                <p>Você solicitou a recuperação de senha para sua conta no sistema SIIA.</p>

                <p>Para redefinir sua senha, clique no link abaixo:</p>

                <a href="{link_recuperacao}" 
                    style="display: inline-block; background-color: #2563eb; color: white; 
                            padding: 12px 24px; text-decoration: none; border-radius: 5px; 
                            margin: 10px 0;">
                    Redefinir Senha
                </a>

                <p>Ou copie e cole o seguinte link no seu navegador:</p>
                <p style="background-color: #f3f4f6; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {link_recuperacao}
                </p>

                <p><strong>Este link é válido por 24 horas.</strong></p>

                <p>Se você não solicitou esta recuperação, ignore este email.</p>

                <hr style="margin: 20px 0; border: none; border-top: 1px solid #e5e5e5;">

                <p style="font-size: 12px; color: #666;">
                    Sistema Integrado de Irrigação Automatizada (SIIA)<br>
                    Instituto Federal da Paraíba
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html_body, 'html'))

        # Conecta ao servidor SMTP e envia o email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Habilita criptografia TLS
        server.login(smtp_username, smtp_password)

        text = msg.as_string()
        server.sendmail(smtp_username, email, text)
        server.quit()

        flash(f"Email de recuperação enviado com sucesso para {email}", 'success')

    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        raise e

if __name__ == '__main__':
    app.run(debug=True)
