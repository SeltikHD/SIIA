--* Estufa *--
CREATE TABLE cultura (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL
);

CREATE TABLE sessao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR NOT NULL,
    cultura_id INTEGER REFERENCES cultura(id) ON DELETE CASCADE
);

CREATE TABLE sessao_irrigacao (
    id SERIAL PRIMARY KEY,
    "status" BOOLEAN NOT NULL,
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,
    sessao_id INTEGER REFERENCES sessao(id) ON DELETE CASCADE
);

CREATE TABLE dado_periodico (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    temperatura FLOAT NOT NULL,
    umidade_ar FLOAT NOT NULL,
    umidade_solo FLOAT NOT NULL,
    imagem BYTEA,
    cultura_id INTEGER REFERENCES cultura(id) ON DELETE CASCADE,
    sessao_id INTEGER REFERENCES sessao(id) ON DELETE CASCADE,
    exaustor_ligado BOOLEAN NOT NULL
);

CREATE TABLE condicao_ideal (
    id SERIAL PRIMARY KEY,
    temperatura_min FLOAT NOT NULL,
    temperatura_max FLOAT NOT NULL,
    umidade_ar_min FLOAT NOT NULL,
    umidade_ar_max FLOAT NOT NULL,
    umidade_solo_min FLOAT NOT NULL,
    umidade_solo_max FLOAT NOT NULL,
    cultura_id INTEGER REFERENCES cultura(id) ON DELETE CASCADE
);

CREATE TABLE controle_exaustao (
    id SERIAL PRIMARY KEY,
    "status" BOOLEAN NOT NULL,
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP
);

CREATE TABLE unidade_medida (
    id SERIAL PRIMARY KEY,
    nome VARCHAR NOT NULL,
    simbolo VARCHAR(5) NOT NULL
);

CREATE TABLE fertilizante (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    unidade_medida_id INTEGER REFERENCES unidade_medida(id) ON DELETE CASCADE
);

CREATE TABLE fertilizante_cultura (
    id SERIAL PRIMARY KEY,
    fertilizante_id INTEGER REFERENCES fertilizante(id) ON DELETE CASCADE,
    cultura_id INTEGER REFERENCES cultura(id) ON DELETE CASCADE,
    quantidade_recomendada FLOAT NOT NULL
);

CREATE TABLE fertilizacao (
    id SERIAL PRIMARY KEY,
    data_aplicacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    quantidade FLOAT NOT NULL,
    fertilizante_cultura_id INTEGER REFERENCES fertilizante_cultura(id) ON DELETE CASCADE
);

--* Usuário *--
CREATE TABLE grupo (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    nivel_acesso INTEGER NOT NULL
);

CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    grupo_id INTEGER REFERENCES grupo(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha TEXT,
    foto BYTEA,
    token_recuperacao TEXT
);

CREATE TABLE log (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE CASCADE,
    mensagem TEXT NOT NULL
);

--* Autenticação *--
CREATE TABLE token (
    id SERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE CASCADE
);

CREATE TABLE sessao_usuario (
    id SERIAL PRIMARY KEY,
    token TEXT NOT NULL,
    data_criacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_expiracao TIMESTAMP NOT NULL default CURRENT_TIMESTAMP + interval '7 day',
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE CASCADE
);

--* Reconhecimento Facial *--
CREATE TABLE tentativa_acesso (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE CASCADE,
    sucesso BOOLEAN NOT NULL,
    foto BYTEA -- Salvar a foto do rosto se a tentativa não for bem sucedida
);

--* Notificação *--
CREATE TABLE notificacao (
    id SERIAL PRIMARY KEY,
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    titulo VARCHAR NOT NULL,
    mensagem VARCHAR NOT NULL
);

CREATE TABLE notificacao_usuario (
    id SERIAL PRIMARY KEY,
    notificacao_id INTEGER REFERENCES notificacao(id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE CASCADE
);

--* Dados Iniciais *--
-- Inserir grupo Administrador Mestre com nível de acesso 5
INSERT INTO grupo (nome, nivel_acesso) VALUES ('Administrador Mestre', 5);

-- Inserir usuário genérico com senha argon2id e atribuir ao grupo Administrador Mestre
INSERT INTO usuario (grupo_id, nome, email, senha) 
VALUES (
    (SELECT id FROM grupo WHERE nome = 'Administrador Mestre'),
    'Administrador',
    'admin@siia.ifpb.edu.br',
    '$argon2id$v=19$m=65536,t=3,p=4$NERNdkhTZXJNY2JLcHFlTw$n48jIzRp1ZDpca0gErLK9w'
);

-- A senha padrão é 'SIIA@AdminPassword' em argon2id

--* Tabelas para controle de dispositivos IoT via MQTT *--
CREATE TABLE status_dispositivo (
    id SERIAL PRIMARY KEY,
    tipo_dispositivo VARCHAR NOT NULL, -- 'irrigacao', 'ventilacao', 'iluminacao'
    status VARCHAR NOT NULL, -- 'LIGADO', 'DESLIGADO', 'ABERTO', 'FECHADO'
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sessao_id INTEGER REFERENCES sessao(id) ON DELETE SET NULL, -- Apenas para irrigacao
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE SET NULL -- Quem ativou manualmente
);

CREATE TABLE comando_dispositivo (
    id SERIAL PRIMARY KEY,
    tipo_dispositivo VARCHAR NOT NULL, -- 'irrigacao', 'ventilacao', 'iluminacao'
    comando VARCHAR NOT NULL, -- 'ON', 'OFF'
    data_hora TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sessao_id INTEGER REFERENCES sessao(id) ON DELETE SET NULL, -- Para irrigacao
    usuario_id INTEGER REFERENCES usuario(id) ON DELETE CASCADE NOT NULL, -- Quem enviou o comando
    executado BOOLEAN DEFAULT FALSE -- Se o comando foi executado com sucesso
);

CREATE TABLE status_mqtt (
    id SERIAL PRIMARY KEY,
    topico VARCHAR NOT NULL, -- Tópico MQTT
    ultima_mensagem TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_conexao BOOLEAN DEFAULT FALSE, -- Se o tópico está ativo
    erro_ultimo VARCHAR -- Último erro registrado para este tópico
);

-- Índices para otimização das consultas MQTT
CREATE INDEX idx_status_dispositivo_tipo_data ON status_dispositivo(tipo_dispositivo, data_hora DESC);
CREATE INDEX idx_comando_dispositivo_usuario_data ON comando_dispositivo(usuario_id, data_hora DESC);
CREATE INDEX idx_status_mqtt_topico ON status_mqtt(topico);
CREATE INDEX idx_dado_periodico_sessao_data ON dado_periodico(sessao_id, data_hora DESC);
