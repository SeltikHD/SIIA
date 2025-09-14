import base64
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

from argon2 import PasswordHasher, exceptions
from dotenv import load_dotenv
from firebase_admin import auth
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from lib.firebase import initialize_firebase
from lib.models import (
    CondicaoIdeal,
    Cultura,
    DadoPeriodico,
    Fertilizacao,
    FertilizanteCultura,
    Fertilizante,
    Grupo,
    Log,
    Sessao,
    SessaoIrrigacao,
    SessaoUsuario,
    TentativaAcesso,
    UnidadeMedida,
    Usuario,
    db,
)

# from lib.mqtt import MQTTClient  # Comentado temporariamente para teste mobile

ph = PasswordHasher()

# * Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

initialize_firebase()

app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///siia.db")
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Faça login para acessar esta página"


@login_manager.user_loader
def load_user(user_id):
    try:
        return Usuario.query.get(int(user_id))
    except Exception:
        return None


# Decoradores de controle de acesso
def admin_required(nivel_minimo=2):
    """Decorator para controlar acesso administrativo baseado no nível do grupo"""

    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.grupo or current_user.grupo.nivel_acesso < nivel_minimo:
                flash(f"Acesso negado. Nível {nivel_minimo} ou superior necessário.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_admin_action(action, detalhes=""):
    """Registra ações administrativas no log"""
    try:
        log_entry = Log(usuario_id=current_user.id, mensagem=f"ADMIN: {action} - {detalhes}")
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar log: {e}")


@app.route("/")
def index():
    sessoes_info = []

    # Consulta todas as sessões
    sessoes = Sessao.query.all()

    for sessao in sessoes:
        # Último dado periódicos da sessão
        ultimo_dado = DadoPeriodico.query.filter_by(sessao_id=sessao.id).order_by(DadoPeriodico.data_hora.desc()).first()

        # Verifica a cultura associada
        cultura = Cultura.query.get(sessao.cultura_id)

        # Verifica se a sessão está sendo irrigada
        irrigacao = SessaoIrrigacao.query.filter_by(sessao_id=sessao.id).order_by(SessaoIrrigacao.data_inicio.desc()).first()
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
        try:
            email = request.form["email"]
            senha = request.form["password"]
            lembrar = request.form.get("remember")
        except KeyError:
            flash("Email e senha são obrigatórios", "error")
            return redirect(url_for("login"))

        # Busca o usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()

        # Verifica se o usuário existe e a senha está correta
        try:
            if usuario:
                if usuario.senha:
                    if ph.verify(usuario.senha, senha):
                        login_user(usuario, remember=lembrar)
                        flash("Login realizado com sucesso", "success")
                        return redirect(url_for("index"))
                    else:
                        flash("Email ou senha inválidos", "error")
                else:
                    flash("Esse usuário não possui senha cadastrada, tente fazer login com Google", "error")
            else:
                flash("Usuário não cadastrado", "error")
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
        # Obtém a URL da imagem de perfil
        photo_url = decoded_token.get("picture")

        if not nome:
            nome = email.split("@")[0].capitalize()

        foto = None
        if photo_url:
            from io import BytesIO

            import requests

            response = requests.get(photo_url)
            # Converte a imagem para bytes
            foto = BytesIO(response.content).getvalue()

        # Verifique se o usuário já existe
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario:
            # Busca o grupo com menor nível de acesso para novos usuários
            grupo_menor_acesso = Grupo.query.order_by(Grupo.nivel_acesso.asc()).first()

            if not grupo_menor_acesso:
                return {"message": "Erro no sistema: nenhum grupo encontrado"}, 500

            # Adiciona a URL da imagem
            usuario = Usuario(nome=nome, email=email, foto=foto, grupo_id=grupo_menor_acesso.id)
            db.session.add(usuario)
            db.session.commit()
        elif (nome or foto) and usuario and (usuario.nome != nome or usuario.foto != foto):
            # Atualizar informações do usuário
            usuario.nome = nome
            usuario.foto = foto
            db.session.commit()

        login_user(usuario)

        return redirect(url_for("index"))  # Redireciona para a página inicial

    except Exception as e:
        print("Erro ao verificar token:", e)
        return {"message": "Falha na autenticação"}, 401


@app.route("/logout")
@login_required
def logout():
    # Limpa a sessão do usuário
    logout_user()
    flash("Logout realizado com sucesso", "success")
    return redirect(url_for("index"))


@app.route("/registrar", methods=["GET", "POST"])
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

        # Busca o grupo com menor nível de acesso
        grupo_menor_acesso = Grupo.query.order_by(Grupo.nivel_acesso.asc()).first()

        if not grupo_menor_acesso:
            flash("Erro no sistema: nenhum grupo encontrado. Entre em contato com o administrador.", "error")
            return render_template("registrar.html")

        # Criptografa a senha
        senha_hash = ph.hash(senha)

        # Cria o novo usuário com o grupo de menor acesso
        novo_usuario = Usuario(nome=nome, email=email, senha=senha_hash, grupo_id=grupo_menor_acesso.id)
        db.session.add(novo_usuario)
        db.session.commit()

        login_user(novo_usuario)
        flash(
            f"Cadastro realizado com sucesso! Você foi atribuído ao grupo '{grupo_menor_acesso.nome}' e já está logado.",
            "success",
        )
        return redirect(url_for("index"))

    return render_template("registrar.html")


@app.route("/perfil")
@login_required
def perfil():
    return render_template("perfil.html")


@app.route("/editar_perfil", methods=["POST"])
@login_required
def editar_perfil():
    try:
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()

        if not nome or not email:
            return jsonify({"success": False, "message": "Nome e email são obrigatórios"})

        # Verifica se o email já está em uso por outro usuário
        if email != current_user.email:
            usuario_existente = Usuario.query.filter_by(email=email).first()
            if usuario_existente:
                return jsonify({"success": False, "message": "Este email já está sendo usado por outro usuário"})

        # Atualiza os dados do usuário
        current_user.nome = nome
        current_user.email = email

        # Processa a foto se foi enviada
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto.filename != "":
                if foto and allowed_file(foto.filename):
                    # Limita o tamanho da imagem (2MB)
                    foto.seek(0, 2)  # Vai para o final do arquivo
                    size = foto.tell()
                    foto.seek(0)  # Volta para o início

                    if size > 2 * 1024 * 1024:  # 2MB
                        return jsonify({"success": False, "message": "A imagem deve ter no máximo 2MB"})

                    current_user.foto = foto.read()
                else:
                    return jsonify({"success": False, "message": "Formato de imagem inválido. Use JPG, JPEG ou PNG"})

        db.session.commit()
        return jsonify({"success": True, "message": "Perfil atualizado com sucesso!"})

    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Erro interno do servidor"})


@app.route("/alterar_senha", methods=["POST"])
@login_required
def alterar_senha():
    try:
        senha_atual = request.form.get("senha_atual", "").strip()
        nova_senha = request.form.get("nova_senha", "").strip()
        confirmar_senha = request.form.get("confirmar_senha", "").strip()

        if not senha_atual or not nova_senha or not confirmar_senha:
            return jsonify({"success": False, "message": "Todos os campos são obrigatórios"})

        if nova_senha != confirmar_senha:
            return jsonify({"success": False, "message": "As senhas não coincidem"})

        if len(nova_senha) < 6:
            return jsonify({"success": False, "message": "A nova senha deve ter pelo menos 6 caracteres"})

        # Verifica se o usuário tem senha (pode ter sido criado via Google)
        if not current_user.senha:
            return jsonify(
                {"success": False, "message": "Este usuário não possui senha. Entre em contato com o administrador"}
            )

        # Verifica a senha atual - CORRIGIDO: ordem dos parâmetros
        try:
            ph.verify(current_user.senha, senha_atual)
        except exceptions.VerifyMismatchError:
            return jsonify({"success": False, "message": "Senha atual incorreta"})
        except exceptions.VerificationError:
            return jsonify({"success": False, "message": "Erro na verificação da senha"})

        # Atualiza a senha
        current_user.senha = ph.hash(nova_senha)
        db.session.commit()

        return jsonify({"success": True, "message": "Senha alterada com sucesso!"})

    except Exception as e:
        db.session.rollback()
        # Para debug - removar em produção
        print(f"Erro na alteração de senha: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"})


@app.route("/esqueci_senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "POST":
        email = request.form.get("email", "").strip()

        if not email:
            flash("Email é obrigatório", "error")
            return render_template("esqueci_senha.html")

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            # Gera token de recuperação
            token = secrets.token_urlsafe(32)
            usuario.token_recuperacao = token
            db.session.commit()

            # Envia email (simulado - em produção usar serviço real)
            try:
                enviar_email_recuperacao(email, token)
                flash("Instruções de recuperação foram enviadas para seu email", "success")
            except Exception:
                flash("Erro ao enviar email. Tente novamente mais tarde", "error")
        else:
            # Por segurança, não revela se o email existe ou não
            flash("Se o email estiver cadastrado, você receberá as instruções de recuperação", "success")

        return redirect(url_for("login"))

    return render_template("esqueci_senha.html")


@app.route("/redefinir_senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    usuario = Usuario.query.filter_by(token_recuperacao=token).first()

    if not usuario:
        flash("Token inválido ou expirado", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        nova_senha = request.form.get("nova_senha", "").strip()
        confirmar_senha = request.form.get("confirmar_senha", "").strip()

        if not nova_senha or not confirmar_senha:
            flash("Todos os campos são obrigatórios", "error")
            return render_template("redefinir_senha.html", token=token)

        if nova_senha != confirmar_senha:
            flash("As senhas não coincidem", "error")
            return render_template("redefinir_senha.html", token=token)

        if len(nova_senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres", "error")
            return render_template("redefinir_senha.html", token=token)

        # Atualiza a senha e remove o token
        usuario.senha = ph.hash(nova_senha)
        usuario.token_recuperacao = None
        db.session.commit()

        flash("Senha redefinida com sucesso! Faça login com sua nova senha", "success")
        return redirect(url_for("login"))

    return render_template("redefinir_senha.html", token=token)


def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def enviar_email_recuperacao(email, token):
    """Envia email real de recuperação de senha via SMTP"""
    try:
        # Configurações SMTP a partir das variáveis de ambiente
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")

        if not all([smtp_server, smtp_username, smtp_password]):
            print("Configurações SMTP incompletas")
            raise ValueError("Configurações SMTP não encontradas")

        # Cria a mensagem de email
        msg = MIMEMultipart()
        msg["From"] = smtp_username
        msg["To"] = email
        msg["Subject"] = "Recuperação de Senha - SIIA"

        # Corpo do email em HTML
        link_recuperacao = f"{os.getenv('SITE_URL')}/redefinir_senha/{token}"
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

        msg.attach(MIMEText(html_body, "html"))

        # Conecta ao servidor SMTP e envia o email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Habilita criptografia TLS
        server.login(smtp_username, smtp_password)

        text = msg.as_string()
        server.sendmail(smtp_username, email, text)
        server.quit()

        flash(f"Email de recuperação enviado com sucesso para {email}", "success")

    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        raise e


# ===== ROTAS ADMINISTRATIVAS =====


@app.route("/admin")
@admin_required(2)
def admin_dashboard():
    """Dashboard administrativo - Nível 2+"""
    stats = {
        "usuarios": Usuario.query.count(),
        "culturas": Cultura.query.count(),
        "sessoes": Sessao.query.count(),
        "fertilizantes": Fertilizante.query.count(),
    }

    # Atividade recente (últimos logs)
    logs_recentes = Log.query.order_by(Log.data_hora.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html", stats=stats, logs_recentes=logs_recentes, nivel_usuario=current_user.grupo.nivel_acesso
    )


# ===== NÍVEL 2: Visualização detalhada =====


@app.route("/admin/culturas")
@admin_required(2)
def admin_culturas_list():
    """Lista de culturas - Nível 2+"""
    culturas = Cultura.query.all()
    return render_template("admin/culturas/list.html", culturas=culturas)


@app.route("/admin/culturas/<int:id>")
@admin_required(2)
def admin_cultura_detail(id):
    """Detalhes de uma cultura - Nível 2+"""
    cultura = Cultura.query.get_or_404(id)
    condicoes = CondicaoIdeal.query.filter_by(cultura_id=id).all()
    sessoes = Sessao.query.filter_by(cultura_id=id).all()

    return render_template("admin/culturas/detail.html", cultura=cultura, condicoes=condicoes, sessoes=sessoes)


@app.route("/admin/sessoes")
@admin_required(2)
def admin_sessoes_list():
    """Lista de sessões - Nível 2+"""
    sessoes = Sessao.query.all()
    return render_template("admin/sessoes/list.html", sessoes=sessoes)


@app.route("/admin/sessoes/<int:id>")
@admin_required(2)
def admin_sessao_detail(id):
    """Detalhes de uma sessão - Nível 2+"""
    sessao = Sessao.query.get_or_404(id)
    dados_recentes = DadoPeriodico.query.filter_by(sessao_id=id).order_by(DadoPeriodico.data_hora.desc()).limit(50).all()
    irrigacoes = SessaoIrrigacao.query.filter_by(sessao_id=id).order_by(SessaoIrrigacao.data_inicio.desc()).all()

    return render_template("admin/sessoes/detail.html", sessao=sessao, dados_recentes=dados_recentes, irrigacoes=irrigacoes)


# ===== NÍVEL 3: CRUD de culturas, condições, fertilizantes =====


@app.route("/admin/culturas/create", methods=["GET", "POST"])
@admin_required(3)
def admin_cultura_create():
    """Criar nova cultura - Nível 3+"""
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()

        if not nome:
            flash("Nome é obrigatório", "error")
            return render_template("admin/culturas/create.html")

        # Verifica se já existe
        if Cultura.query.filter_by(nome=nome).first():
            flash("Já existe uma cultura com este nome", "error")
            return render_template("admin/culturas/create.html")

        cultura = Cultura(nome=nome)
        db.session.add(cultura)
        db.session.commit()

        log_admin_action("Cultura criada", f"Nome: {nome}")
        flash("Cultura criada com sucesso!", "success")
        return redirect(url_for("admin_culturas_list"))

    return render_template("admin/culturas/create.html")


@app.route("/admin/culturas/<int:id>/edit", methods=["GET", "POST"])
@admin_required(3)
def admin_cultura_edit(id):
    """Editar cultura - Nível 3+"""
    cultura = Cultura.query.get_or_404(id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()

        if not nome:
            flash("Nome é obrigatório", "error")
            return render_template("admin/culturas/edit.html", cultura=cultura)

        # Verifica se já existe outro com o mesmo nome
        existente = Cultura.query.filter_by(nome=nome).filter(Cultura.id != id).first()
        if existente:
            flash("Já existe uma cultura com este nome", "error")
            return render_template("admin/culturas/edit.html", cultura=cultura)

        nome_antigo = cultura.nome
        cultura.nome = nome
        db.session.commit()

        log_admin_action("Cultura editada", f"ID: {id}, Nome: {nome_antigo} -> {nome}")
        flash("Cultura atualizada com sucesso!", "success")
        return redirect(url_for("admin_cultura_detail", id=id))

    return render_template("admin/culturas/edit.html", cultura=cultura)


@app.route("/admin/culturas/<int:id>/delete", methods=["POST"])
@admin_required(3)
def admin_cultura_delete(id):
    """Deletar cultura - Nível 3+"""
    cultura = Cultura.query.get_or_404(id)

    nome = cultura.nome

    try:
        # Remove sessões e seus dados relacionados (irrigação e dados periódicos)
        sessoes = Sessao.query.filter_by(cultura_id=id).all()
        for sessao in sessoes:
            DadoPeriodico.query.filter_by(sessao_id=sessao.id).delete()
            SessaoIrrigacao.query.filter_by(sessao_id=sessao.id).delete()
            db.session.delete(sessao)

        # Por segurança, remove dados periódicos que referenciem diretamente a cultura
        DadoPeriodico.query.filter_by(cultura_id=id).delete()

        # Remove associações de fertilizantes e registros de fertilização
        assoc_list = FertilizanteCultura.query.filter_by(cultura_id=id).all()
        for assoc in assoc_list:
            Fertilizacao.query.filter_by(fertilizante_cultura_id=assoc.id).delete()
        FertilizanteCultura.query.filter_by(cultura_id=id).delete()

        # Remove condições ideais associadas
        CondicaoIdeal.query.filter_by(cultura_id=id).delete()

        # Finalmente, remove a cultura
        db.session.delete(cultura)
        db.session.commit()

        log_admin_action("Cultura deletada", f"ID: {id}, Nome: {nome}")
        flash("Cultura deletada com sucesso!", "success")
        return redirect(url_for("admin_culturas_list"))
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar cultura {id}: {e}")
        flash("Erro ao deletar cultura. Verifique dependências e tente novamente.", "error")
        return redirect(url_for("admin_cultura_detail", id=id))


@app.route("/admin/condicoes-ideais")
@admin_required(3)
def admin_condicoes_list():
    """Lista de condições ideais - Nível 3+"""
    condicoes = CondicaoIdeal.query.all()
    return render_template("admin/condicoes/list.html", condicoes=condicoes)


@app.route("/admin/condicoes-ideais/create", methods=["GET", "POST"])
@admin_required(3)
def admin_condicao_create():
    """Criar condição ideal - Nível 3+"""
    if request.method == "POST":
        try:
            cultura_id = int(request.form.get("cultura_id"))
            temp_min = float(request.form.get("temperatura_min"))
            temp_max = float(request.form.get("temperatura_max"))
            umid_ar_min = float(request.form.get("umidade_ar_min"))
            umid_ar_max = float(request.form.get("umidade_ar_max"))
            umid_solo_min = float(request.form.get("umidade_solo_min"))
            umid_solo_max = float(request.form.get("umidade_solo_max"))

            # Validações
            if temp_min >= temp_max:
                flash("Temperatura mínima deve ser menor que a máxima", "error")
                raise ValueError()

            if umid_ar_min >= umid_ar_max:
                flash("Umidade do ar mínima deve ser menor que a máxima", "error")
                raise ValueError()

            if umid_solo_min >= umid_solo_max:
                flash("Umidade do solo mínima deve ser menor que a máxima", "error")
                raise ValueError()

            # Verifica se já existe condição para esta cultura
            if CondicaoIdeal.query.filter_by(cultura_id=cultura_id).first():
                flash("Já existe uma condição ideal para esta cultura", "error")
                raise ValueError()

            condicao = CondicaoIdeal(
                cultura_id=cultura_id,
                temperatura_min=temp_min,
                temperatura_max=temp_max,
                umidade_ar_min=umid_ar_min,
                umidade_ar_max=umid_ar_max,
                umidade_solo_min=umid_solo_min,
                umidade_solo_max=umid_solo_max,
            )

            db.session.add(condicao)
            db.session.commit()

            cultura = Cultura.query.get(cultura_id)
            log_admin_action("Condição ideal criada", f"Cultura: {cultura.nome}")
            flash("Condição ideal criada com sucesso!", "success")
            return redirect(url_for("admin_condicoes_list"))

        except (ValueError, TypeError):
            pass

    culturas = Cultura.query.all()
    return render_template("admin/condicoes/create.html", culturas=culturas)


@app.route("/admin/fertilizantes")
@admin_required(3)
def admin_fertilizantes_list():
    """Lista de fertilizantes - Nível 3+"""
    fertilizantes = Fertilizante.query.all()
    return render_template("admin/fertilizantes/list.html", fertilizantes=fertilizantes)


@app.route("/admin/fertilizantes/create", methods=["GET", "POST"])
@admin_required(3)
def admin_fertilizante_create():
    """Criar fertilizante - Nível 3+"""
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        unidade_medida_id = request.form.get("unidade_medida_id")

        if not nome:
            flash("Nome é obrigatório", "error")
            return render_template("admin/fertilizantes/create.html")

        if not unidade_medida_id:
            flash("Unidade de medida é obrigatória", "error")
            return render_template("admin/fertilizantes/create.html")

        try:
            unidade_medida_id = int(unidade_medida_id)
        except ValueError:
            flash("Unidade de medida inválida", "error")
            return render_template("admin/fertilizantes/create.html")

        # Verifica se já existe
        if Fertilizante.query.filter_by(nome=nome).first():
            flash("Já existe um fertilizante com este nome", "error")
            return render_template("admin/fertilizantes/create.html")

        fertilizante = Fertilizante(nome=nome, unidade_medida_id=unidade_medida_id)
        db.session.add(fertilizante)
        db.session.commit()

        log_admin_action("Fertilizante criado", f"Nome: {nome}")
        flash("Fertilizante criado com sucesso!", "success")
        return redirect(url_for("admin_fertilizantes_list"))

    unidades = UnidadeMedida.query.all()
    return render_template("admin/fertilizantes/create.html", unidades=unidades)


@app.route("/admin/fertilizantes/<int:id>/edit", methods=["GET", "POST"])
@admin_required(3)
def admin_fertilizante_edit(id):
    """Editar fertilizante - Nível 3+"""
    fertilizante = Fertilizante.query.get_or_404(id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        unidade_medida_id = request.form.get("unidade_medida_id")

        if not nome:
            flash("Nome é obrigatório", "error")
            return render_template("admin/fertilizantes/edit.html", fertilizante=fertilizante)

        if not unidade_medida_id:
            flash("Unidade de medida é obrigatória", "error")
            return render_template("admin/fertilizantes/edit.html", fertilizante=fertilizante)

        try:
            unidade_medida_id = int(unidade_medida_id)
        except ValueError:
            flash("Unidade de medida inválida", "error")
            return render_template("admin/fertilizantes/edit.html", fertilizante=fertilizante)

        # Verifica se já existe outro com o mesmo nome
        existente = Fertilizante.query.filter_by(nome=nome).filter(Fertilizante.id != id).first()
        if existente:
            flash("Já existe um fertilizante com este nome", "error")
            return render_template("admin/fertilizantes/edit.html", fertilizante=fertilizante)

        nome_antigo = fertilizante.nome
        fertilizante.nome = nome
        fertilizante.unidade_medida_id = unidade_medida_id
        db.session.commit()

        log_admin_action("Fertilizante editado", f"ID: {id}, Nome: {nome_antigo} -> {nome}")
        flash("Fertilizante atualizado com sucesso!", "success")
        return redirect(url_for("admin_fertilizantes_list"))

    unidades = UnidadeMedida.query.all()
    return render_template("admin/fertilizantes/edit.html", fertilizante=fertilizante, unidades=unidades)


@app.route("/admin/fertilizantes/<int:id>/delete", methods=["POST"])
@admin_required(3)
def admin_fertilizante_delete(id):
    """Deletar fertilizante - Nível 3+"""
    fertilizante = Fertilizante.query.get_or_404(id)

    # Verifica se tem culturas associadas
    if fertilizante.culturas:
        flash("Não é possível deletar um fertilizante que possui culturas associadas", "error")
        return redirect(url_for("admin_fertilizantes_list"))

    nome = fertilizante.nome

    db.session.delete(fertilizante)
    db.session.commit()

    log_admin_action("Fertilizante deletado", f"ID: {id}, Nome: {nome}")
    flash("Fertilizante deletado com sucesso!", "success")
    return redirect(url_for("admin_fertilizantes_list"))


@app.route("/admin/unidades-medida")
@admin_required(3)
def admin_unidades_list():
    """Lista de unidades de medida - Nível 3+"""
    unidades = UnidadeMedida.query.all()
    return render_template("admin/unidades/list.html", unidades=unidades)


@app.route("/admin/unidades-medida/create", methods=["GET", "POST"])
@admin_required(3)
def admin_unidade_create():
    """Criar unidade de medida - Nível 3+"""
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        simbolo = request.form.get("simbolo", "").strip()

        if not nome or not simbolo:
            flash("Nome e símbolo são obrigatórios", "error")
            return render_template("admin/unidades/create.html")

        # Verifica se já existe
        if UnidadeMedida.query.filter_by(nome=nome).first():
            flash("Já existe uma unidade com este nome", "error")
            return render_template("admin/unidades/create.html")

        if UnidadeMedida.query.filter_by(simbolo=simbolo).first():
            flash("Já existe uma unidade com este símbolo", "error")
            return render_template("admin/unidades/create.html")

        unidade = UnidadeMedida(nome=nome, simbolo=simbolo)
        db.session.add(unidade)
        db.session.commit()

        log_admin_action("Unidade de medida criada", f"Nome: {nome}, Símbolo: {simbolo}")
        flash("Unidade de medida criada com sucesso!", "success")
        return redirect(url_for("admin_unidades_list"))

    return render_template("admin/unidades/create.html")


@app.route("/admin/unidades-medida/<int:id>/edit", methods=["GET", "POST"])
@admin_required(3)
def admin_unidade_edit(id):
    """Editar unidade de medida - Nível 3+"""
    unidade = UnidadeMedida.query.get_or_404(id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        simbolo = request.form.get("simbolo", "").strip()

        if not nome or not simbolo:
            flash("Nome e símbolo são obrigatórios", "error")
            return render_template("admin/unidades/edit.html", unidade=unidade)

        # Verifica se já existe outro com o mesmo nome
        existente_nome = UnidadeMedida.query.filter_by(nome=nome).filter(UnidadeMedida.id != id).first()
        if existente_nome:
            flash("Já existe uma unidade com este nome", "error")
            return render_template("admin/unidades/edit.html", unidade=unidade)

        existente_simbolo = UnidadeMedida.query.filter_by(simbolo=simbolo).filter(UnidadeMedida.id != id).first()
        if existente_simbolo:
            flash("Já existe uma unidade com este símbolo", "error")
            return render_template("admin/unidades/edit.html", unidade=unidade)

        nome_antigo = unidade.nome
        simbolo_antigo = unidade.simbolo
        unidade.nome = nome
        unidade.simbolo = simbolo
        db.session.commit()

        log_admin_action(
            "Unidade de medida editada", f"ID: {id}, Nome: {nome_antigo} -> {nome}, Símbolo: {simbolo_antigo} -> {simbolo}"
        )
        flash("Unidade de medida atualizada com sucesso!", "success")
        return redirect(url_for("admin_unidades_list"))

    return render_template("admin/unidades/edit.html", unidade=unidade)


@app.route("/admin/unidades-medida/<int:id>/delete", methods=["POST"])
@admin_required(3)
def admin_unidade_delete(id):
    """Deletar unidade de medida - Nível 3+"""
    unidade = UnidadeMedida.query.get_or_404(id)

    # Verifica se tem fertilizantes associados
    if unidade.fertilizantes:
        flash("Não é possível deletar uma unidade que possui fertilizantes associados", "error")
        return redirect(url_for("admin_unidades_list"))

    nome = unidade.nome
    simbolo = unidade.simbolo

    db.session.delete(unidade)
    db.session.commit()

    log_admin_action("Unidade de medida deletada", f"ID: {id}, Nome: {nome}, Símbolo: {simbolo}")
    flash("Unidade de medida deletada com sucesso!", "success")
    return redirect(url_for("admin_unidades_list"))


# ===== NÍVEL 4: CRUD de sessões =====


@app.route("/admin/sessoes/create", methods=["GET", "POST"])
@admin_required(4)
def admin_sessao_create():
    """Criar nova sessão - Nível 4+"""
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cultura_id = request.form.get("cultura_id")

        if not nome:
            flash("Nome é obrigatório", "error")
            return render_template("admin/sessoes/create.html")

        if not cultura_id:
            flash("Cultura é obrigatória", "error")
            return render_template("admin/sessoes/create.html")

        try:
            cultura_id = int(cultura_id)
        except ValueError:
            flash("Cultura inválida", "error")
            return render_template("admin/sessoes/create.html")

        # Verifica se já existe sessão com este nome
        if Sessao.query.filter_by(nome=nome).first():
            flash("Já existe uma sessão com este nome", "error")
            return render_template("admin/sessoes/create.html")

        sessao = Sessao(nome=nome, cultura_id=cultura_id)
        db.session.add(sessao)
        db.session.commit()

        cultura = Cultura.query.get(cultura_id)
        log_admin_action("Sessão criada", f"Nome: {nome}, Cultura: {cultura.nome}")
        flash("Sessão criada com sucesso!", "success")
        return redirect(url_for("admin_sessoes_list"))

    culturas = Cultura.query.all()
    return render_template("admin/sessoes/create.html", culturas=culturas)


@app.route("/admin/sessoes/<int:id>/edit", methods=["GET", "POST"])
@admin_required(4)
def admin_sessao_edit(id):
    """Editar sessão - Nível 4+"""
    sessao = Sessao.query.get_or_404(id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        cultura_id = request.form.get("cultura_id")

        if not nome:
            flash("Nome é obrigatório", "error")
            return render_template("admin/sessoes/edit.html", sessao=sessao)

        if not cultura_id:
            flash("Cultura é obrigatória", "error")
            return render_template("admin/sessoes/edit.html", sessao=sessao)

        try:
            cultura_id = int(cultura_id)
        except ValueError:
            flash("Cultura inválida", "error")
            return render_template("admin/sessoes/edit.html", sessao=sessao)

        # Verifica se já existe outra sessão com este nome
        existente = Sessao.query.filter_by(nome=nome).filter(Sessao.id != id).first()
        if existente:
            flash("Já existe uma sessão com este nome", "error")
            return render_template("admin/sessoes/edit.html", sessao=sessao)

        nome_antigo = sessao.nome
        cultura_antiga = sessao.cultura.nome

        sessao.nome = nome
        sessao.cultura_id = cultura_id
        db.session.commit()

        cultura_nova = Cultura.query.get(cultura_id)
        log_admin_action(
            "Sessão editada", f"ID: {id}, Nome: {nome_antigo} -> {nome}, Cultura: {cultura_antiga} -> {cultura_nova.nome}"
        )
        flash("Sessão atualizada com sucesso!", "success")
        return redirect(url_for("admin_sessao_detail", id=id))

    culturas = Cultura.query.all()
    return render_template("admin/sessoes/edit.html", sessao=sessao, culturas=culturas)


@app.route("/admin/sessoes/<int:id>/delete", methods=["POST"])
@admin_required(4)
def admin_sessao_delete(id):
    """Deletar sessão - Nível 4+"""
    sessao = Sessao.query.get_or_404(id)

    nome = sessao.nome
    cultura_nome = sessao.cultura.nome

    # Remove dados relacionados
    DadoPeriodico.query.filter_by(sessao_id=id).delete()
    SessaoIrrigacao.query.filter_by(sessao_id=id).delete()

    db.session.delete(sessao)
    db.session.commit()

    log_admin_action("Sessão deletada", f"ID: {id}, Nome: {nome}, Cultura: {cultura_nome}")
    flash("Sessão deletada com sucesso!", "success")
    return redirect(url_for("admin_sessoes_list"))


# ===== NÍVEL 5: Gerenciamento de usuários e logs =====


@app.route("/admin/usuarios")
@admin_required(5)
def admin_usuarios_list():
    """Lista de usuários - Nível 5+"""
    usuarios = Usuario.query.all()
    grupos = Grupo.query.all()
    return render_template("admin/usuarios/list.html", usuarios=usuarios, grupos=grupos)


@app.route("/admin/usuarios/<int:id>/edit", methods=["GET", "POST"])
@admin_required(5)
def admin_usuario_edit(id):
    """Editar usuário - Nível 5+"""
    usuario = Usuario.query.get_or_404(id)

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        grupo_id = request.form.get("grupo_id")

        if not nome or not email:
            flash("Nome e email são obrigatórios", "error")
            return render_template("admin/usuarios/edit.html", usuario=usuario)

        try:
            grupo_id = int(grupo_id)
        except (ValueError, TypeError):
            flash("Grupo inválido", "error")
            return render_template("admin/usuarios/edit.html", usuario=usuario)

        # Verifica se email já está em uso por outro usuário
        existente = Usuario.query.filter_by(email=email).filter(Usuario.id != id).first()
        if existente:
            flash("Este email já está sendo usado por outro usuário", "error")
            return render_template("admin/usuarios/edit.html", usuario=usuario)

        nome_antigo = usuario.nome
        email_antigo = usuario.email
        grupo_antigo = usuario.grupo.nome

        usuario.nome = nome
        usuario.email = email
        usuario.grupo_id = grupo_id
        db.session.commit()

        grupo_novo = Grupo.query.get(grupo_id)
        log_admin_action(
            "Usuário editado",
            f"ID: {id}, Nome: {nome_antigo} -> {nome}, Email: {email_antigo} -> {email}, Grupo: {grupo_antigo} -> {grupo_novo.nome}",
        )
        flash("Usuário atualizado com sucesso!", "success")
        return redirect(url_for("admin_usuarios_list"))

    grupos = Grupo.query.all()
    return render_template("admin/usuarios/edit.html", usuario=usuario, grupos=grupos)


@app.route("/admin/usuarios/<int:id>/delete", methods=["POST"])
@admin_required(5)
def admin_usuario_delete(id):
    """Deletar usuário - Nível 5+"""
    usuario = Usuario.query.get_or_404(id)

    # Não pode deletar a si mesmo
    if usuario.id == current_user.id:
        flash("Você não pode deletar sua própria conta", "error")
        return redirect(url_for("admin_usuarios_list"))

    nome = usuario.nome
    email = usuario.email

    # Remove dados relacionados
    Log.query.filter_by(usuario_id=id).delete()
    TentativaAcesso.query.filter_by(usuario_id=id).delete()

    db.session.delete(usuario)
    db.session.commit()

    log_admin_action("Usuário deletado", f"ID: {id}, Nome: {nome}, Email: {email}")
    flash("Usuário deletado com sucesso!", "success")
    return redirect(url_for("admin_usuarios_list"))


@app.route("/admin/logs")
@admin_required(5)
def admin_logs_list():
    """Lista de logs - Nível 5+"""
    page = request.args.get("page", 1, type=int)
    per_page = 50

    logs = Log.query.order_by(Log.data_hora.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template("admin/logs/list.html", logs=logs)


# ===== API ENDPOINTS MÓVEIS =====


@app.route("/api/mobile/login", methods=["POST"])
def api_mobile_login():
    """Endpoint de login para aplicativo móvel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400

        email = data.get("email", "").strip()
        senha = data.get("password", "") or data.get("senha", "")  # Aceita ambos os campos

        if not email or not senha:
            return jsonify({"success": False, "message": "Email e senha são obrigatórios"}), 400

        # Busca o usuário pelo email
        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.senha:
            return jsonify({"success": False, "message": "Credenciais inválidas"}), 401

        # Verifica a senha
        try:
            if ph.verify(usuario.senha, senha):
                # Gera token de sessão para mobile
                token = secrets.token_urlsafe(32)

                # Cria ou atualiza sessão móvel
                sessao_mobile = SessaoUsuario.query.filter_by(usuario_id=usuario.id).first()
                if sessao_mobile:
                    sessao_mobile.token = token
                    sessao_mobile.data_criacao = datetime.now()
                    sessao_mobile.data_expiracao = datetime.now() + timedelta(days=7)
                else:
                    sessao_mobile = SessaoUsuario(
                        token=token, usuario_id=usuario.id, data_expiracao=datetime.now() + timedelta(days=7)
                    )
                    db.session.add(sessao_mobile)

                db.session.commit()

                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Login realizado com sucesso",
                            "token": token,
                            "usuario": {
                                "id": usuario.id,
                                "nome": usuario.nome,
                                "email": usuario.email,
                                "grupo": (
                                    {
                                        "id": usuario.grupo.id,
                                        "nome": usuario.grupo.nome,
                                        "nivel_acesso": usuario.grupo.nivel_acesso,
                                    }
                                    if usuario.grupo
                                    else None
                                ),
                                "foto_base64": usuario.foto_base64,
                            },
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"success": False, "message": "Credenciais inválidas"}), 401

        except exceptions.VerifyMismatchError:
            return jsonify({"success": False, "message": "Credenciais inválidas"}), 401

    except Exception as e:
        print(f"Erro no login móvel: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


@app.route("/api/mobile/logout", methods=["POST"])
def api_mobile_logout():
    """Endpoint de logout para aplicativo móvel"""
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")

        if token:
            # Remove a sessão móvel
            sessao_mobile = SessaoUsuario.query.filter_by(token=token).first()
            if sessao_mobile:
                db.session.delete(sessao_mobile)
                db.session.commit()

        return jsonify({"success": True, "message": "Logout realizado com sucesso"}), 200

    except Exception as e:
        print(f"Erro no logout móvel: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


@app.route("/api/mobile/dashboard", methods=["GET"])
def api_mobile_dashboard():
    """Endpoint de dados do dashboard para aplicativo móvel"""
    try:
        # Verifica autenticação
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"success": False, "message": "Token não fornecido"}), 401

        sessao_mobile = SessaoUsuario.query.filter_by(token=token).first()
        if not sessao_mobile or sessao_mobile.data_expiracao < datetime.now():
            return jsonify({"success": False, "message": "Token inválido ou expirado"}), 401

        # Busca dados das sessões
        sessoes_info = []
        sessoes = Sessao.query.all()

        for sessao_cultivo in sessoes:
            # Último dado periódico da sessão
            ultimo_dado = (
                DadoPeriodico.query.filter_by(sessao_id=sessao_cultivo.id).order_by(DadoPeriodico.data_hora.desc()).first()
            )

            # Verifica a cultura associada
            cultura = Cultura.query.get(sessao_cultivo.cultura_id)

            # Verifica se a sessão está sendo irrigada
            irrigacao = (
                SessaoIrrigacao.query.filter_by(sessao_id=sessao_cultivo.id)
                .order_by(SessaoIrrigacao.data_inicio.desc())
                .first()
            )
            esta_irrigando = irrigacao.status if irrigacao else False

            # Cálculo de tempo de cultivo
            tempo_cultivo = None
            if irrigacao and irrigacao.data_inicio:
                tempo_cultivo = (datetime.now() - irrigacao.data_inicio).days

            # Prepara a imagem em base64
            imagem_base64 = None
            if ultimo_dado and ultimo_dado.imagem:
                imagem_base64 = base64.b64encode(ultimo_dado.imagem).decode("utf-8")

            sessoes_info.append(
                {
                    "id": sessao_cultivo.id,
                    "nome": sessao_cultivo.nome,
                    "cultura": {"id": cultura.id if cultura else None, "nome": cultura.nome if cultura else "Sem cultura"},
                    "tempo_cultivo": tempo_cultivo,
                    "ocupada": bool(cultura),
                    "esta_irrigando": esta_irrigando,
                    "dados": {
                        "temperatura": ultimo_dado.temperatura if ultimo_dado else None,
                        "umidade_ar": ultimo_dado.umidade_ar if ultimo_dado else None,
                        "umidade_solo": ultimo_dado.umidade_solo if ultimo_dado else None,
                        "data_hora": ultimo_dado.data_hora.isoformat() if ultimo_dado else None,
                    },
                    "imagem_base64": imagem_base64,
                }
            )

        return (
            jsonify(
                {"success": True, "data": sessoes_info}  # Mudado de "sessoes" para "data" para compatibilidade com mobile
            ),
            200,
        )

    except Exception as e:
        print(f"Erro no dashboard móvel: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


@app.route("/api/mobile/culturas", methods=["GET"])
def api_mobile_culturas():
    """Endpoint de culturas para aplicativo móvel"""
    try:
        # Verifica autenticação
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"success": False, "message": "Token não fornecido"}), 401

        sessao_mobile = SessaoUsuario.query.filter_by(token=token).first()
        if not sessao_mobile or sessao_mobile.data_expiracao < datetime.now():
            return jsonify({"success": False, "message": "Token inválido ou expirado"}), 401

        # Busca culturas
        culturas = Cultura.query.all()
        culturas_data = []

        for cultura in culturas:
            culturas_data.append(
                {
                    "id": cultura.id,
                    "nome": cultura.nome,
                    "temperatura_ideal": "20-25°C",
                    "umidade_ideal": "60-80%",
                    "ph_ideal": "6.0-7.0",
                }
            )

        return jsonify({"success": True, "culturas": culturas_data}), 200

    except Exception as e:
        print(f"Erro nas culturas móvel: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


@app.route("/api/mobile/usuarios", methods=["GET"])
def api_mobile_usuarios():
    """Endpoint de usuários para aplicativo móvel (admin apenas)"""
    try:
        # Verifica autenticação
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"success": False, "message": "Token não fornecido"}), 401

        sessao_mobile = SessaoUsuario.query.filter_by(token=token).first()
        if not sessao_mobile or sessao_mobile.data_expiracao < datetime.now():
            return jsonify({"success": False, "message": "Token inválido ou expirado"}), 401

        # Verifica se é admin (nível 2+ pode ver usuários)
        usuario = Usuario.query.get(sessao_mobile.usuario_id)
        if not usuario or not usuario.grupo or usuario.grupo.nivel_acesso < 2:
            return jsonify({"success": False, "message": "Acesso negado - Necessário nível de administrador"}), 403

        # Busca usuários
        usuarios = Usuario.query.all()
        usuarios_data = []

        for user in usuarios:
            usuarios_data.append(
                {
                    "id": user.id,
                    "nome": user.nome,
                    "email": user.email,
                    "grupo": {
                        "id": user.grupo.id if user.grupo else None,
                        "nome": user.grupo.nome if user.grupo else None,
                        "nivel_acesso": user.grupo.nivel_acesso if user.grupo else None,
                    },
                    "foto_base64": user.foto_base64,
                    "tem_senha": bool(user.senha),
                }
            )

        return jsonify({"success": True, "usuarios": usuarios_data}), 200

    except Exception as e:
        print(f"Erro nos usuários móvel: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


@app.route("/api/mobile/register", methods=["POST"])
def api_mobile_register():
    """Endpoint de registro para aplicativo móvel"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400

        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        senha = data.get("password", "") or data.get("senha", "")  # Aceita ambos os campos

        if not nome or not email or not senha:
            return jsonify({"success": False, "message": "Nome, email e senha são obrigatórios"}), 400

        if len(senha) < 6:
            return jsonify({"success": False, "message": "A senha deve ter pelo menos 6 caracteres"}), 400

        # Verifica se email já existe
        if Usuario.query.filter_by(email=email).first():
            return jsonify({"success": False, "message": "Este email já está sendo usado"}), 409

        # Busca grupo padrão (nível 1)
        grupo_padrao = Grupo.query.filter_by(nivel_acesso=1).first()
        if not grupo_padrao:
            return jsonify({"success": False, "message": "Erro de configuração do sistema"}), 500

        # Cria novo usuário
        novo_usuario = Usuario(nome=nome, email=email, senha=ph.hash(senha), grupo_id=grupo_padrao.id)

        db.session.add(novo_usuario)
        db.session.commit()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Usuário criado com sucesso",
                    "usuario": {"id": novo_usuario.id, "nome": novo_usuario.nome, "email": novo_usuario.email},
                }
            ),
            201,
        )

    except Exception as e:
        print(f"Erro no registro móvel: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


@app.route("/api/mobile/perfil", methods=["GET"])
def api_mobile_perfil():
    """Endpoint de perfil para aplicativo móvel (usuário logado)"""
    try:
        # Verifica autenticação
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"success": False, "message": "Token não fornecido"}), 401

        sessao_mobile = SessaoUsuario.query.filter_by(token=token).first()
        if not sessao_mobile or sessao_mobile.data_expiracao < datetime.now():
            return jsonify({"success": False, "message": "Token inválido ou expirado"}), 401

        # Busca dados do usuário logado
        usuario = Usuario.query.get(sessao_mobile.usuario_id)
        if not usuario:
            return jsonify({"success": False, "message": "Usuário não encontrado"}), 404

        # Estatísticas do sistema para o usuário
        stats = {
            "total_culturas": Cultura.query.count(),
            "total_usuarios": Usuario.query.count(),
            "total_sessoes": Sessao.query.count(),
        }

        # Dados do usuário
        usuario_data = {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "grupo": {
                "id": usuario.grupo.id if usuario.grupo else None,
                "nome": usuario.grupo.nome if usuario.grupo else None,
                "nivel_acesso": usuario.grupo.nivel_acesso if usuario.grupo else None,
            },
            "foto_base64": usuario.foto_base64,
            "data_criacao": (
                usuario.data_criacao.isoformat() if hasattr(usuario, "data_criacao") and usuario.data_criacao else None
            ),
        }

        return jsonify({"success": True, "usuario": usuario_data, "estatisticas": stats}), 200

    except Exception as e:
        print(f"Erro no perfil móvel: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
