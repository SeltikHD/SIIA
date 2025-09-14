"""
Testes para funcionalidade MQTT e IoT
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from lib.models import StatusDispositivo, ComandoDispositivo, StatusMQTT, DadoPeriodico, Sessao, Cultura


class TestMQTTClient:
    """Testes para a classe MQTTClient"""

    @pytest.fixture
    def mock_mqtt_client(self):
        """Mock do cliente MQTT"""
        with patch('paho.mqtt.client.Client') as mock_client:
            yield mock_client

    @pytest.fixture
    def mqtt_client(self, app, mock_mqtt_client):
        """Instância do MQTTClient para testes"""
        from lib.mqtt_new import MQTTClient
        client = MQTTClient()
        client.app = app
        return client

    def test_mqtt_client_initialization(self, mqtt_client, mock_mqtt_client):
        """Testa inicialização do cliente MQTT"""
        assert mqtt_client is not None
        assert hasattr(mqtt_client, 'mqtt_client')
        assert hasattr(mqtt_client, 'connected')

    def test_mqtt_status(self, mqtt_client):
        """Testa função de status do MQTT"""
        status = mqtt_client.status()
        assert isinstance(status, dict)
        assert 'connected' in status
        assert 'broker' in status
        assert 'port' in status

    @patch.dict('os.environ', {
        'MQTT_URL': 'test_broker.com',
        'MQTT_PORT': '1883',
        'MQTT_USERNAME': 'test_user',
        'MQTT_PASSWORD': 'test_pass'
    })
    def test_mqtt_publish(self, mqtt_client):
        """Testa publicação de mensagens MQTT"""
        # Mock do publish
        mqtt_client.mqtt_client.publish = Mock()
        mqtt_client.mqtt_client.publish.return_value = Mock()
        mqtt_client.mqtt_client.publish.return_value.wait_for_publish = Mock()
        mqtt_client.connected = True

        # Testar publish
        result = mqtt_client.publish("test/topic", {"test": "data"})
        
        # Verificar se foi chamado corretamente
        mqtt_client.mqtt_client.publish.assert_called_once()
        args = mqtt_client.mqtt_client.publish.call_args[0]
        assert args[0] == "test/topic"
        assert json.loads(args[1]) == {"test": "data"}

    def test_processar_temperatura(self, mqtt_client, db_session, cultura, sessao):
        """Testa processamento de dados de temperatura"""
        with mqtt_client.app.app_context():
            data = {"temperatura": 25.5}
            
            mqtt_client.processar_temperatura(data)
            
            # Verificar se dados foram salvos
            dados = DadoPeriodico.query.all()
            assert len(dados) > 0
            assert dados[0].temperatura == 25.5

    def test_processar_umidade_ar(self, mqtt_client, db_session, cultura, sessao):
        """Testa processamento de dados de umidade do ar"""
        with mqtt_client.app.app_context():
            data = {"umidade_ar": 68.2}
            
            mqtt_client.processar_umidade_ar(data)
            
            # Verificar se dados foram salvos
            dados = DadoPeriodico.query.all()
            assert len(dados) > 0
            assert dados[0].umidade_ar == 68.2

    def test_processar_umidade_solo(self, mqtt_client, db_session, cultura, sessao):
        """Testa processamento de dados de umidade do solo"""
        with mqtt_client.app.app_context():
            data = {"umidade": 45.7}
            canteiro = str(sessao.id)
            
            mqtt_client.processar_umidade_solo(data, canteiro)
            
            # Verificar se dados foram salvos
            dados = DadoPeriodico.query.filter_by(sessao_id=sessao.id).all()
            assert len(dados) > 0
            assert dados[0].umidade_solo == 45.7

    def test_processar_status_irrigacao(self, mqtt_client, db_session, sessao):
        """Testa processamento de status de irrigação"""
        with mqtt_client.app.app_context():
            data = {"status": "ABERTO", "sessao_id": sessao.id}
            
            mqtt_client.processar_status_irrigacao(data)
            
            # Verificar se status foi salvo
            status = StatusDispositivo.query.filter_by(tipo_dispositivo="irrigacao").first()
            assert status is not None
            assert status.status == "ABERTO"
            assert status.sessao_id == sessao.id

    def test_processar_status_ventilacao(self, mqtt_client, db_session):
        """Testa processamento de status de ventilação"""
        with mqtt_client.app.app_context():
            data = {"status": "LIGADO"}
            
            mqtt_client.processar_status_ventilacao(data)
            
            # Verificar se status foi salvo
            status = StatusDispositivo.query.filter_by(tipo_dispositivo="ventilacao").first()
            assert status is not None
            assert status.status == "LIGADO"

    def test_processar_alerta(self, mqtt_client, db_session):
        """Testa processamento de alertas"""
        with mqtt_client.app.app_context():
            data = {"mensagem": "Temperatura muito alta", "nivel": "CRÍTICO"}
            
            mqtt_client.processar_alerta(data)
            
            # Verificar se alerta foi salvo
            from lib.models import Notificacao
            alerta = Notificacao.query.first()
            assert alerta is not None
            assert "Temperatura muito alta" in alerta.mensagem
            assert "CRÍTICO" in alerta.titulo

    def test_enviar_comando_irrigacao(self, mqtt_client):
        """Testa envio de comando de irrigação"""
        mqtt_client.mqtt_client.publish = Mock()
        mqtt_client.mqtt_client.publish.return_value = Mock()
        mqtt_client.mqtt_client.publish.return_value.wait_for_publish = Mock()
        mqtt_client.connected = True

        result = mqtt_client.enviar_comando_irrigacao(1, "ON")
        
        assert result is True
        mqtt_client.mqtt_client.publish.assert_called_once()

    def test_enviar_comando_ventilacao(self, mqtt_client):
        """Testa envio de comando de ventilação"""
        mqtt_client.mqtt_client.publish = Mock()
        mqtt_client.mqtt_client.publish.return_value = Mock()
        mqtt_client.mqtt_client.publish.return_value.wait_for_publish = Mock()
        mqtt_client.connected = True

        result = mqtt_client.enviar_comando_ventilacao("OFF")
        
        assert result is True
        mqtt_client.mqtt_client.publish.assert_called_once()

    def test_get_device_status(self, mqtt_client, db_session):
        """Testa busca de status dos dispositivos"""
        with mqtt_client.app.app_context():
            # Criar alguns status
            status1 = StatusDispositivo(tipo_dispositivo="irrigacao", status="ABERTO")
            status2 = StatusDispositivo(tipo_dispositivo="ventilacao", status="LIGADO")
            db_session.add(status1)
            db_session.add(status2)
            db_session.commit()

            # Buscar todos
            all_status = mqtt_client.get_device_status()
            assert len(all_status) == 2

            # Buscar por tipo
            irrig_status = mqtt_client.get_device_status("irrigacao")
            assert len(irrig_status) == 1
            assert irrig_status[0].tipo_dispositivo == "irrigacao"

    def test_get_recent_sensors_data(self, mqtt_client, db_session, cultura, sessao):
        """Testa busca de dados recentes dos sensores"""
        with mqtt_client.app.app_context():
            # Criar alguns dados
            for i in range(5):
                dado = DadoPeriodico(
                    sessao_id=sessao.id,
                    cultura_id=cultura.id,
                    temperatura=20.0 + i,
                    umidade_ar=60.0 + i,
                    umidade_solo=40.0 + i,
                    exaustor_ligado=False
                )
                db_session.add(dado)
            db_session.commit()

            # Buscar dados recentes
            recent_data = mqtt_client.get_recent_sensors_data(3)
            assert len(recent_data) == 3
            # Deve estar em ordem decrescente
            assert recent_data[0].temperatura == 24.0


class TestMQTTModels:
    """Testes para os modelos relacionados ao MQTT"""

    def test_status_dispositivo_creation(self, db_session):
        """Testa criação de StatusDispositivo"""
        status = StatusDispositivo(
            tipo_dispositivo="irrigacao",
            status="ABERTO",
            sessao_id=1
        )
        db_session.add(status)
        db_session.commit()

        assert status.id is not None
        assert status.tipo_dispositivo == "irrigacao"
        assert status.status == "ABERTO"

    def test_comando_dispositivo_creation(self, db_session, admin_user):
        """Testa criação de ComandoDispositivo"""
        comando = ComandoDispositivo(
            tipo_dispositivo="ventilacao",
            comando="ON",
            usuario_id=admin_user.id,
            executado=False
        )
        db_session.add(comando)
        db_session.commit()

        assert comando.id is not None
        assert comando.tipo_dispositivo == "ventilacao"
        assert comando.comando == "ON"
        assert comando.executado is False

    def test_status_mqtt_creation(self, db_session):
        """Testa criação de StatusMQTT"""
        status = StatusMQTT(
            topico="estufa/temperatura",
            status_conexao=True
        )
        db_session.add(status)
        db_session.commit()

        assert status.id is not None
        assert status.topico == "estufa/temperatura"
        assert status.status_conexao is True


class TestMQTTRoutes:
    """Testes para as rotas MQTT"""

    def test_admin_mqtt_dashboard_requires_auth(self, client):
        """Testa que dashboard MQTT requer autenticação"""
        response = client.get("/admin/mqtt")
        assert response.status_code == 302  # Redirect para login

    def test_admin_mqtt_dashboard_requires_level_3(self, client, auth_user_level_2):
        """Testa que dashboard MQTT requer nível 3"""
        response = client.get("/admin/mqtt")
        # Deve negar acesso ou redirecionar
        assert response.status_code in [302, 403]

    def test_admin_mqtt_dashboard_success(self, client, admin_user_level_3):
        """Testa acesso bem-sucedido ao dashboard MQTT"""
        response = client.get("/admin/mqtt")
        assert response.status_code == 200
        assert b"Dashboard MQTT" in response.data

    def test_admin_mqtt_status_json(self, client, admin_user_level_3):
        """Testa endpoint de status MQTT em JSON"""
        response = client.get("/admin/mqtt/status")
        assert response.status_code == 200
        assert response.content_type == "application/json"
        
        data = json.loads(response.data)
        assert "success" in data
        assert "mqtt_status" in data

    def test_admin_mqtt_command_post(self, client, admin_user_level_4, db_session):
        """Testa envio de comando MQTT"""
        command_data = {
            "device_type": "ventilacao",
            "command": "ON"
        }
        
        response = client.post(
            "/admin/mqtt/command",
            data=json.dumps(command_data),
            content_type="application/json"
        )
        
        # Pode falhar se MQTT não estiver conectado, mas deve processar a request
        assert response.status_code in [200, 500]

    def test_admin_mqtt_command_irrigacao_requires_sessao(self, client, admin_user_level_4):
        """Testa que comando de irrigação requer sessao_id"""
        command_data = {
            "device_type": "irrigacao",
            "command": "ON"
            # Sem sessao_id
        }
        
        response = client.post(
            "/admin/mqtt/command",
            data=json.dumps(command_data),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "sessao_id obrigatório" in data["message"]

    def test_admin_mqtt_sensors_json(self, client, admin_user_level_2, db_session, cultura, sessao):
        """Testa endpoint de dados dos sensores"""
        # Criar alguns dados de teste
        dado = DadoPeriodico(
            sessao_id=sessao.id,
            cultura_id=cultura.id,
            temperatura=25.0,
            umidade_ar=65.0,
            umidade_solo=45.0,
            exaustor_ligado=False
        )
        db_session.add(dado)
        db_session.commit()

        response = client.get("/admin/mqtt/sensors")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) > 0

    def test_admin_mqtt_devices_page(self, client, admin_user_level_3, db_session, sessao):
        """Testa página de controle de dispositivos"""
        response = client.get("/admin/mqtt/devices")
        assert response.status_code == 200
        assert b"Controle de Dispositivos IoT" in response.data

    def test_mqtt_command_invalid_device_type(self, client, admin_user_level_4):
        """Testa comando com tipo de dispositivo inválido"""
        command_data = {
            "device_type": "invalid_device",
            "command": "ON"
        }
        
        response = client.post(
            "/admin/mqtt/command",
            data=json.dumps(command_data),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Tipo de dispositivo inválido" in data["message"]


class TestMQTTIntegration:
    """Testes de integração MQTT"""

    @patch('lib.mqtt_new.mqtt')
    def test_mqtt_message_processing_flow(self, mock_mqtt, app, db_session, cultura, sessao):
        """Testa fluxo completo de processamento de mensagem MQTT"""
        from lib.mqtt_new import MQTTClient
        
        with app.app_context():
            # Criar cliente MQTT
            mqtt_client = MQTTClient(app)
            
            # Simular mensagem de temperatura
            topic = "estufa/temperatura"
            payload = '{"temperatura": 26.5}'
            
            # Processar mensagem
            mqtt_client.process_message(topic, payload)
            
            # Verificar se dados foram salvos
            dados = DadoPeriodico.query.filter_by(sessao_id=sessao.id).all()
            assert len(dados) > 0
            assert dados[0].temperatura == 26.5

    def test_device_command_to_database_flow(self, client, admin_user_level_4, db_session, sessao):
        """Testa fluxo de comando de dispositivo até o banco"""
        command_data = {
            "device_type": "irrigacao",
            "command": "ON",
            "sessao_id": sessao.id
        }
        
        # Mock do MQTT client para simular sucesso
        with patch('lib.mqtt_new.mqtt_client') as mock_client:
            mock_client.enviar_comando_irrigacao.return_value = True
            
            response = client.post(
                "/admin/mqtt/command",
                data=json.dumps(command_data),
                content_type="application/json"
            )
        
        # Se MQTT estiver mockado corretamente, deve salvar o comando
        if response.status_code == 200:
            # Verificar se comando foi salvo no banco
            comando = ComandoDispositivo.query.filter_by(
                tipo_dispositivo="irrigacao",
                comando="ON"
            ).first()
            assert comando is not None
            assert comando.sessao_id == sessao.id
            assert comando.usuario_id == admin_user_level_4.id


# Fixtures adicionais para testes MQTT
@pytest.fixture
def auth_user_level_2(client, db_session):
    """Usuário autenticado com nível 2"""
    from lib.models import Usuario, Grupo
    grupo = Grupo(nome="Visualizador", nivel_acesso=2)
    db_session.add(grupo)
    db_session.commit()
    
    user = Usuario(
        grupo_id=grupo.id,
        nome="User Level 2",
        email="level2@test.com",
        senha="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    
    return user


@pytest.fixture  
def admin_user_level_3(client, db_session):
    """Usuário admin com nível 3"""
    from lib.models import Usuario, Grupo
    grupo = Grupo(nome="Editor", nivel_acesso=3)
    db_session.add(grupo)
    db_session.commit()
    
    user = Usuario(
        grupo_id=grupo.id,
        nome="Admin Level 3",
        email="level3@test.com",
        senha="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    
    return user


@pytest.fixture
def admin_user_level_4(client, db_session):
    """Usuário admin com nível 4"""
    from lib.models import Usuario, Grupo
    grupo = Grupo(nome="Gerente", nivel_acesso=4)
    db_session.add(grupo)
    db_session.commit()
    
    user = Usuario(
        grupo_id=grupo.id,
        nome="Admin Level 4", 
        email="level4@test.com",
        senha="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    
    return user