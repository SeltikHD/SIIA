import json
import logging
import uuid
import threading
import ssl
from os import getenv
from base64 import b64decode

import paho.mqtt.client as mqtt
from flask import current_app as app

# Configurações do Broker MQTT
MQTT_BROKER = getenv("MQTT_URL")
MQTT_PORT = int(getenv("MQTT_PORT", 8883))
MQTT_USERNAME = getenv("MQTT_USERNAME")
MQTT_PASSWORD = getenv("MQTT_PASSWORD")

MQTT_TOPICS = {
    "temperatura": "estufa/temperatura",
    "umidade_ar": "estufa/umidade/ar",
    "umidade_solo": "estufa/umidade/solo/#",
    "camera": "estufa/camera/imagem",
    "irrigacao_status": "estufa/irrigacao/status",
    "ventilacao_status": "estufa/ventilacao/status",
    "iluminacao_status": "estufa/iluminacao/status",
    "alerta": "estufa/alerta",
    "irrigacao_manual": "estufa/irrigacao/manual",
    "ventilacao_manual": "estufa/ventilacao/manual",
    "iluminacao_manual": "estufa/iluminacao/manual",
}


class MQTTClient:
    def __init__(self):
        self.mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311, client_id=f"FlaskClient-{uuid.uuid4()}")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.connected = False
        
        # Configurar TLS para HiveMQ Cloud
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.mqtt_client.tls_set_context(context)
        
        # Configurar credenciais
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        # Iniciar conexão com o broker
        self.connect_broker()

    def connect_broker(self):
        try:
            if MQTT_BROKER and MQTT_PORT:
                logging.info(f"Tentando conectar ao broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
                self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
                
                # Iniciar o loop MQTT em segundo plano
                self.mqtt_thread = threading.Thread(target=self.mqtt_client.loop_forever)
                self.mqtt_thread.daemon = True
                self.mqtt_thread.start()
            else:
                logging.warning("Configurações MQTT não encontradas no .env")
        except Exception as e:
            logging.error(f"Erro ao conectar ao broker MQTT: {e}")
            self.connected = False

    # Verificar status da conexão
    def status(self):
        return self.mqtt_client.is_connected()

    # Publicar mensagem em um tópico
    def publish(self, topic, payload, qos=1):
        try:
            result = self.mqtt_client.publish(topic, json.dumps(payload), qos)
            result.wait_for_publish()
            logging.info(f"Mensagem publicada no tópico {topic}: {payload}")
        except Exception as e:
            logging.error(f"Erro ao publicar mensagem no tópico {topic}: {e}")

    # Callback para conexão
    def on_connect(self, client, _userdata, _flags, rc, _properties=None):
        logging.info(f"Conectado ao Broker MQTT com código: {rc}")
        # Subscreve aos tópicos necessários
        for topic in MQTT_TOPICS.values():
            client.subscribe(topic)
            logging.info(f"Inscrito no tópico: {topic}")

    # Callback para mensagens recebidas
    def on_message(self, _client, _userdata, msg, _properties=None):
        try:
            logging.info(f"Mensagem recebida no tópico {msg.topic}: {msg.payload.decode()}")
            self.process_message(msg.topic, msg.payload.decode())
        except Exception as e:
            logging.error(f"Erro ao processar mensagem do tópico {msg.topic}: {e}")

    # Callback para desconexão
    def on_disconnect(self, _client, _userdata, rc, _properties=None):
        if rc != 0:
            logging.warning(f"Conexão perdida com o Broker MQTT. Código de retorno: {rc}. Tentando reconectar...")
            try:
                self.mqtt_client.reconnect()
            except Exception as e:
                logging.error(f"Erro ao tentar reconectar ao Broker MQTT: {e}")
        else:
            logging.info("Desconexão limpa do Broker MQTT.")

    def process_message(self, topic, payload):
        # Usando o contexto de aplicação Flask
        data = json.loads(payload)
        try:
            # Cria um contexto de aplicação Flask
            with app.app_context():
                if topic == MQTT_TOPICS["temperatura"]:
                    self.salvar_dado_periodico(data, tipo="temperatura")
                elif topic == MQTT_TOPICS["umidade_ar"]:
                    self.salvar_dado_periodico(data, tipo="umidade_ar")
                elif topic.startswith("estufa/umidade/solo/"):
                    self.salvar_dado_periodico(data, tipo="umidade_solo", sessao_id=topic.split("/")[-1])
                elif topic == MQTT_TOPICS["camera"]:
                    self.processar_imagem(data)
                elif topic == MQTT_TOPICS["alerta"]:
                    self.criar_alerta(data)
                else:
                    logging.warning(f"Tópico não reconhecido: {topic}")
        except Exception as e:
            logging.error(f"Erro ao processar mensagem: {e}")

    def salvar_dado_periodico(self, data, tipo, sessao_id=None):
        sessao = Sessao.query.filter_by(id=int(sessao_id)).first() if sessao_id else None
        if sessao or tipo in ["temperatura", "umidade_ar"]:
            try:
                novo_dado = DadoPeriodico(
                    sessao_id=sessao.id if sessao else None,
                    temperatura=data.get("temperatura"),
                    umidade_ar=data.get("umidade_ar"),
                    umidade_solo=data.get("umidade"),
                )
                db.session.add(novo_dado)
                db.session.commit()
                logging.info(f"Dado periódico salvo ({tipo}): {novo_dado}")
            except Exception as e:
                logging.error(f"Erro ao salvar dado periódico ({tipo}): {e}")

    def processar_imagem(self, _data):
        # Salvamento de imagens processadas
        logging.info("Imagem recebida e processada (implementação pendente).")

    def criar_alerta(self, data):
        alerta = Notificacao(
            titulo="Alerta Crítico na Estufa",
            mensagem=data.get("mensagem", "Alerta recebido."),
        )
        db.session.add(alerta)
        db.session.commit()
        logging.info(f"Alerta salvo: {alerta}")
