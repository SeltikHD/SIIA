from base64 import b64encode

from flask_sqlalchemy import SQLAlchemy

# * Constants
USUARIO_ID = "usuario.id"
CULTURA_ID = "cultura.id"

db = SQLAlchemy()


# ? Tabelas relacionadas à estufa
class Cultura(db.Model):
    __tablename__ = "cultura"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    condicoes_ideais = db.relationship("CondicaoIdeal", backref="cultura", lazy=True)
    sessoes = db.relationship("Sessao", backref="cultura", lazy=True)

    def __str__(self):
        return self.nome


class Sessao(db.Model):
    __tablename__ = "sessao"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    cultura_id = db.Column(db.Integer, db.ForeignKey(CULTURA_ID), nullable=False)
    irrigacoes = db.relationship("SessaoIrrigacao", backref="sessao", lazy=True)
    dados_periodicos = db.relationship("DadoPeriodico", backref="sessao", lazy=True)


class SessaoIrrigacao(db.Model):
    __tablename__ = "sessao_irrigacao"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, nullable=False)
    data_inicio = db.Column(db.TIMESTAMP)
    data_fim = db.Column(db.TIMESTAMP)
    sessao_id = db.Column(db.Integer, db.ForeignKey("sessao.id"), nullable=False)


class DadoPeriodico(db.Model):
    __tablename__ = "dado_periodico"
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    temperatura = db.Column(db.Float, nullable=False)
    umidade_ar = db.Column(db.Float, nullable=False)
    umidade_solo = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.LargeBinary)
    cultura_id = db.Column(db.Integer, db.ForeignKey(CULTURA_ID), nullable=False)
    sessao_id = db.Column(db.Integer, db.ForeignKey("sessao.id"), nullable=False)
    exaustor_ligado = db.Column(db.Boolean, nullable=False)


class CondicaoIdeal(db.Model):
    __tablename__ = "condicao_ideal"
    id = db.Column(db.Integer, primary_key=True)
    temperatura_min = db.Column(db.Float, nullable=False)
    temperatura_max = db.Column(db.Float, nullable=False)
    umidade_ar_min = db.Column(db.Float, nullable=False)
    umidade_ar_max = db.Column(db.Float, nullable=False)
    umidade_solo_min = db.Column(db.Float, nullable=False)
    umidade_solo_max = db.Column(db.Float, nullable=False)
    cultura_id = db.Column(db.Integer, db.ForeignKey(CULTURA_ID), nullable=False)


class ControleExaustao(db.Model):
    __tablename__ = "controle_exaustao"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, nullable=False)
    data_inicio = db.Column(db.TIMESTAMP)
    data_fim = db.Column(db.TIMESTAMP)


# ? Tabelas de fertilizantes e fertilização
class UnidadeMedida(db.Model):
    __tablename__ = "unidade_medida"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    simbolo = db.Column(db.String(5), nullable=False)
    fertilizantes = db.relationship("Fertilizante", backref="unidade_medida", lazy=True)

    def __str__(self):
        return f"{self.nome} ({self.simbolo})"


class Fertilizante(db.Model):
    __tablename__ = "fertilizante"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    unidade_medida_id = db.Column(db.Integer, db.ForeignKey("unidade_medida.id"), nullable=False)
    culturas = db.relationship("FertilizanteCultura", backref="fertilizante", lazy=True)


class FertilizanteCultura(db.Model):
    __tablename__ = "fertilizante_cultura"
    id = db.Column(db.Integer, primary_key=True)
    fertilizante_id = db.Column(db.Integer, db.ForeignKey("fertilizante.id"), nullable=False)
    cultura_id = db.Column(db.Integer, db.ForeignKey(CULTURA_ID), nullable=False)
    quantidade_recomendada = db.Column(db.Float, nullable=False)
    cultura = db.relationship("Cultura", backref="fertilizante_culturas", lazy=True)


class Fertilizacao(db.Model):
    __tablename__ = "fertilizacao"
    id = db.Column(db.Integer, primary_key=True)
    data_aplicacao = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    quantidade = db.Column(db.Float, nullable=False)
    fertilizante_cultura_id = db.Column(db.Integer, db.ForeignKey("fertilizante_cultura.id"), nullable=False)


# ? Tabelas de usuários e autenticação
class Grupo(db.Model):
    __tablename__ = "grupo"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    nivel_acesso = db.Column(db.Integer, nullable=False)
    usuarios = db.relationship("Usuario", backref="grupo", lazy=True)

    def __str__(self):
        return self.nome


class Usuario(db.Model):
    __tablename__ = "usuario"
    id = db.Column(db.Integer, primary_key=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey("grupo.id"), nullable=False)
    nome = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    senha = db.Column(db.String)
    foto = db.Column(db.LargeBinary)
    token_recuperacao = db.Column(db.String)
    logs = db.relationship("Log", backref="usuario", lazy=True)
    tentativas_acesso = db.relationship("TentativaAcesso", backref="usuario", lazy=True)
    notificacoes = db.relationship("NotificacaoUsuario", backref="usuario", lazy=True)

    # ? Atributos / Métodos do Flask-Login
    is_authenticated = True
    is_active = True
    is_anonymous = False

    @property
    def foto_base64(self):
        if self.foto:
            return b64encode(self.foto).decode("utf-8")
        return None

    def get_id(self):
        return self.id


class Log(db.Model):
    usuario_id = db.Column(db.Integer, db.ForeignKey(USUARIO_ID), nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    usuario_id = db.Column(db.Integer, db.ForeignKey(USUARIO_ID), nullable=False)
    mensagem = db.Column(db.String, nullable=False)


class Token(db.Model):
    __tablename__ = "token"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey(USUARIO_ID), nullable=False)


class SessaoUsuario(db.Model):
    __tablename__ = "sessao_usuario"
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, nullable=False)
    data_criacao = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    data_expiracao = db.Column(
        db.TIMESTAMP, nullable=False, default=db.func.current_timestamp() + db.text("interval '7 days'")
    )
    usuario_id = db.Column(db.Integer, db.ForeignKey(USUARIO_ID), nullable=False)


# ? Tabelas de reconhecimento facial e notificações
class TentativaAcesso(db.Model):
    __tablename__ = "tentativa_acesso"
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    usuario_id = db.Column(db.Integer, db.ForeignKey(USUARIO_ID), nullable=False)
    sucesso = db.Column(db.Boolean, nullable=False)
    foto = db.Column(db.LargeBinary)


class Notificacao(db.Model):
    __tablename__ = "notificacao"
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.TIMESTAMP, nullable=False, default=db.func.current_timestamp())
    titulo = db.Column(db.String, nullable=False)
    mensagem = db.Column(db.String, nullable=False)


class NotificacaoUsuario(db.Model):
    __tablename__ = "notificacao_usuario"
    id = db.Column(db.Integer, primary_key=True)
    notificacao_id = db.Column(db.Integer, db.ForeignKey("notificacao.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey(USUARIO_ID), nullable=False)
