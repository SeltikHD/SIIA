import json
import logging
import uuid
import threading
import ssl
from os import getenv
from base64 import b64decode
from datetime import datetime

import paho.mqtt.client as mqtt

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
    def __init__(self, app=None):
        self.app = app
        self.mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311, client_id=f"FlaskClient-{uuid.uuid4()}")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.connected = False
        self.last_error = None
        
        # Configurar TLS para HiveMQ Cloud
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.mqtt_client.tls_set_context(context)
        
        # Configurar credenciais
        if MQTT_USERNAME and MQTT_PASSWORD:
            self.mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        # Iniciar conexão com o broker
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.mqtt_client = self
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
            self.last_error = str(e)
            self.update_mqtt_status("DESCONECTADO", str(e))

    def status(self):
        return {
            'connected': self.connected,
            'broker': MQTT_BROKER,
            'port': MQTT_PORT,
            'last_error': self.last_error
        }

    def publish(self, topic, payload, qos=1):
        try:
            if not self.connected:
                logging.warning("MQTT não conectado. Tentando reconectar...")
                return False
            
            result = self.mqtt_client.publish(topic, json.dumps(payload), qos)
            result.wait_for_publish()
            logging.info(f"Mensagem publicada no tópico {topic}: {payload}")
            return True
        except Exception as e:
            logging.error(f"Erro ao publicar mensagem no tópico {topic}: {e}")
            return False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.last_error = None
            logging.info("Conectado ao Broker MQTT com sucesso!")
            
            # Subscrever aos tópicos necessários
            for topic_name, topic in MQTT_TOPICS.items():
                try:
                    client.subscribe(topic)
                    logging.info(f"Inscrito no tópico: {topic}")
                except Exception as e:
                    logging.error(f"Erro ao se inscrever no tópico {topic}: {e}")
                    
            # Atualizar status na base de dados
            self.update_mqtt_status("CONECTADO")
        else:
            self.connected = False
            error_messages = {
                1: "Versão de protocolo incorreta",
                2: "ID de cliente inválido",
                3: "Servidor indisponível",
                4: "Usuário ou senha incorretos",
                5: "Não autorizado"
            }
            error_msg = error_messages.get(rc, f"Erro desconhecido: {rc}")
            self.last_error = error_msg
            logging.error(f"Falha na conexão MQTT: {error_msg}")
            self.update_mqtt_status("DESCONECTADO", error_msg)

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            logging.info(f"Mensagem recebida no tópico {topic}: {payload}")
            
            # Processar mensagem com contexto Flask
            if self.app:
                with self.app.app_context():
                    self.process_message(topic, payload)
            else:
                logging.warning("App context não disponível para processar mensagem")
                
        except Exception as e:
            logging.error(f"Erro ao processar mensagem do tópico {msg.topic}: {e}")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            logging.warning(f"Conexão perdida com o Broker MQTT. Código: {rc}. Tentando reconectar...")
            self.last_error = f"Desconexão inesperada: {rc}"
            self.update_mqtt_status("DESCONECTADO", self.last_error)
            # Tentar reconectar após 5 segundos
            threading.Timer(5.0, self.reconnect).start()
        else:
            logging.info("Desconexão limpa do Broker MQTT.")
            self.update_mqtt_status("DESCONECTADO")

    def reconnect(self):
        try:
            logging.info("Tentando reconectar ao MQTT...")
            self.mqtt_client.reconnect()
        except Exception as e:
            logging.error(f"Erro ao tentar reconectar: {e}")
            # Tentar novamente em 30 segundos
            threading.Timer(30.0, self.reconnect).start()

    def process_message(self, topic, payload):
        try:
            # Import here to avoid circular imports
            from lib.models import (
                db, DadoPeriodico, Notificacao, Sessao, StatusDispositivo, StatusMQTT
            )
            
            data = json.loads(payload)
            
            # Atualizar último recebimento no tópico
            status_mqtt = StatusMQTT.query.filter_by(topico=topic).first()
            if not status_mqtt:
                status_mqtt = StatusMQTT(topico=topic, status_conexao=True)
                db.session.add(status_mqtt)
            else:
                status_mqtt.ultima_mensagem = datetime.utcnow()
                status_mqtt.status_conexao = True
                status_mqtt.erro_ultimo = None
                
            # Processar por tipo de tópico
            if topic == MQTT_TOPICS["temperatura"]:
                self.processar_temperatura(data)
                
            elif topic == MQTT_TOPICS["umidade_ar"]:
                self.processar_umidade_ar(data)
                
            elif topic.startswith("estufa/umidade/solo/"):
                canteiro = topic.split("/")[-1]
                self.processar_umidade_solo(data, canteiro)
                
            elif topic == MQTT_TOPICS["camera"]:
                self.processar_imagem(data)
                
            elif topic == MQTT_TOPICS["irrigacao_status"]:
                self.processar_status_irrigacao(data)
                
            elif topic == MQTT_TOPICS["ventilacao_status"]:
                self.processar_status_ventilacao(data)
                
            elif topic == MQTT_TOPICS["iluminacao_status"]:
                self.processar_status_iluminacao(data)
                
            elif topic == MQTT_TOPICS["alerta"]:
                self.processar_alerta(data)
                
            else:
                logging.warning(f"Tópico não reconhecido: {topic}")
                
            db.session.commit()
            
        except json.JSONDecodeError:
            logging.error(f"Payload JSON inválido para tópico {topic}: {payload}")
        except Exception as e:
            logging.error(f"Erro ao processar mensagem: {e}")
            try:
                db.session.rollback()
            except:
                pass

    def processar_temperatura(self, data):
        from lib.models import db, DadoPeriodico, Sessao
        
        temperatura = data.get("temperatura")
        if temperatura is not None:
            # Salvar para todas as sessões ativas
            sessoes_ativas = Sessao.query.all()  # Implementar lógica de sessões ativas
            
            for sessao in sessoes_ativas:
                # Buscar último dado para manter outros valores
                ultimo_dado = DadoPeriodico.query.filter_by(
                    sessao_id=sessao.id
                ).order_by(DadoPeriodico.data_hora.desc()).first()
                
                novo_dado = DadoPeriodico(
                    sessao_id=sessao.id,
                    cultura_id=sessao.cultura_id,
                    temperatura=temperatura,
                    umidade_ar=ultimo_dado.umidade_ar if ultimo_dado else 0.0,
                    umidade_solo=ultimo_dado.umidade_solo if ultimo_dado else 0.0,
                    exaustor_ligado=ultimo_dado.exaustor_ligado if ultimo_dado else False
                )
                db.session.add(novo_dado)
            
            logging.info(f"Temperatura processada: {temperatura}°C")

    def processar_umidade_ar(self, data):
        from lib.models import db, DadoPeriodico, Sessao
        
        umidade_ar = data.get("umidade_ar")
        if umidade_ar is not None:
            # Salvar para todas as sessões ativas
            sessoes_ativas = Sessao.query.all()
            
            for sessao in sessoes_ativas:
                ultimo_dado = DadoPeriodico.query.filter_by(
                    sessao_id=sessao.id
                ).order_by(DadoPeriodico.data_hora.desc()).first()
                
                novo_dado = DadoPeriodico(
                    sessao_id=sessao.id,
                    cultura_id=sessao.cultura_id,
                    temperatura=ultimo_dado.temperatura if ultimo_dado else 0.0,
                    umidade_ar=umidade_ar,
                    umidade_solo=ultimo_dado.umidade_solo if ultimo_dado else 0.0,
                    exaustor_ligado=ultimo_dado.exaustor_ligado if ultimo_dado else False
                )
                db.session.add(novo_dado)
            
            logging.info(f"Umidade do ar processada: {umidade_ar}%")

    def processar_umidade_solo(self, data, canteiro):
        from lib.models import db, DadoPeriodico, Sessao
        
        umidade_solo = data.get("umidade")
        if umidade_solo is not None:
            try:
                # Assumir que canteiro corresponde ao sessao_id
                sessao_id = int(canteiro)
                sessao = Sessao.query.filter_by(id=sessao_id).first()
                
                if sessao:
                    ultimo_dado = DadoPeriodico.query.filter_by(
                        sessao_id=sessao.id
                    ).order_by(DadoPeriodico.data_hora.desc()).first()
                    
                    novo_dado = DadoPeriodico(
                        sessao_id=sessao.id,
                        cultura_id=sessao.cultura_id,
                        temperatura=ultimo_dado.temperatura if ultimo_dado else 0.0,
                        umidade_ar=ultimo_dado.umidade_ar if ultimo_dado else 0.0,
                        umidade_solo=umidade_solo,
                        exaustor_ligado=ultimo_dado.exaustor_ligado if ultimo_dado else False
                    )
                    db.session.add(novo_dado)
                    
                    logging.info(f"Umidade do solo processada para canteiro {canteiro}: {umidade_solo}%")
                else:
                    logging.warning(f"Sessão {sessao_id} não encontrada para canteiro {canteiro}")
                    
            except ValueError:
                logging.error(f"ID de canteiro inválido: {canteiro}")

    def processar_imagem(self, data):
        from lib.models import db, DadoPeriodico, Sessao
        
        imagem_base64 = data.get("imagem")
        if imagem_base64:
            try:
                # Decodificar imagem base64
                imagem_bytes = b64decode(imagem_base64)
                
                # Salvar para todas as sessões ativas (ou implementar lógica específica)
                sessoes_ativas = Sessao.query.all()
                
                for sessao in sessoes_ativas:
                    ultimo_dado = DadoPeriodico.query.filter_by(
                        sessao_id=sessao.id
                    ).order_by(DadoPeriodico.data_hora.desc()).first()
                    
                    if ultimo_dado:
                        ultimo_dado.imagem = imagem_bytes
                    else:
                        # Criar novo registro se não existir
                        novo_dado = DadoPeriodico(
                            sessao_id=sessao.id,
                            cultura_id=sessao.cultura_id,
                            temperatura=0.0,
                            umidade_ar=0.0,
                            umidade_solo=0.0,
                            exaustor_ligado=False,
                            imagem=imagem_bytes
                        )
                        db.session.add(novo_dado)
                
                logging.info("Imagem processada e salva")
                
            except Exception as e:
                logging.error(f"Erro ao processar imagem: {e}")

    def processar_status_irrigacao(self, data):
        from lib.models import db, StatusDispositivo
        
        status = data.get("status")
        sessao_id = data.get("sessao_id")
        
        if status:
            status_device = StatusDispositivo(
                tipo_dispositivo="irrigacao",
                status=status,
                sessao_id=sessao_id
            )
            db.session.add(status_device)
            logging.info(f"Status irrigação: {status} para sessão {sessao_id}")

    def processar_status_ventilacao(self, data):
        from lib.models import db, StatusDispositivo
        
        status = data.get("status")
        
        if status:
            status_device = StatusDispositivo(
                tipo_dispositivo="ventilacao",
                status=status
            )
            db.session.add(status_device)
            logging.info(f"Status ventilação: {status}")

    def processar_status_iluminacao(self, data):
        from lib.models import db, StatusDispositivo
        
        status = data.get("status")
        
        if status:
            status_device = StatusDispositivo(
                tipo_dispositivo="iluminacao",
                status=status
            )
            db.session.add(status_device)
            logging.info(f"Status iluminação: {status}")

    def processar_alerta(self, data):
        from lib.models import db, Notificacao
        
        mensagem = data.get("mensagem", "Alerta recebido")
        nivel = data.get("nivel", "INFO")
        
        alerta = Notificacao(
            titulo=f"Alerta {nivel} na Estufa",
            mensagem=mensagem
        )
        db.session.add(alerta)
        logging.info(f"Alerta criado: {mensagem}")

    def update_mqtt_status(self, status, error_message=None):
        """Atualiza o status da conexão MQTT no banco de dados"""
        try:
            if not self.app:
                return
                
            # Usar contexto da aplicação Flask
            with self.app.app_context():
                # Importar apenas quando necessário para evitar import circular
                from lib.models import StatusMQTT, db
                
                # Buscar registro existente ou criar novo
                mqtt_status = StatusMQTT.query.first()
                if not mqtt_status:
                    mqtt_status = StatusMQTT()
                    db.session.add(mqtt_status)
                
                mqtt_status.status = status
                mqtt_status.ultima_conexao = datetime.now()
                mqtt_status.mensagem_erro = error_message
                
                db.session.commit()
                
        except Exception as e:
            logging.error(f"Erro ao atualizar status MQTT: {e}")

    # Métodos para envio de comandos manuais
    def enviar_comando_irrigacao(self, sessao_id, comando):
        """Enviar comando manual de irrigação"""
        topic = MQTT_TOPICS["irrigacao_manual"]
        payload = {
            "sessao_id": sessao_id,
            "comando": comando
        }
        return self.publish(topic, payload, qos=2)

    def enviar_comando_ventilacao(self, comando):
        """Enviar comando manual de ventilação"""
        topic = MQTT_TOPICS["ventilacao_manual"]
        payload = {
            "comando": comando
        }
        return self.publish(topic, payload, qos=2)

    def enviar_comando_iluminacao(self, comando):
        """Enviar comando manual de iluminação"""
        topic = MQTT_TOPICS["iluminacao_manual"]
        payload = {
            "comando": comando
        }
        return self.publish(topic, payload, qos=1)

    def get_device_status(self, tipo_dispositivo=None):
        """Buscar status atual dos dispositivos"""
        try:
            from lib.models import StatusDispositivo
            
            query = StatusDispositivo.query
            if tipo_dispositivo:
                query = query.filter_by(tipo_dispositivo=tipo_dispositivo)
            
            return query.order_by(StatusDispositivo.data_hora.desc()).all()
            
        except Exception as e:
            logging.error(f"Erro ao buscar status dos dispositivos: {e}")
            return []

    def get_recent_sensors_data(self, limit=10):
        """Buscar dados recentes dos sensores"""
        try:
            from lib.models import DadoPeriodico
            
            return DadoPeriodico.query.order_by(
                DadoPeriodico.data_hora.desc()
            ).limit(limit).all()
            
        except Exception as e:
            logging.error(f"Erro ao buscar dados dos sensores: {e}")
            return []


# Instância global para uso na aplicação
mqtt_client = MQTTClient()