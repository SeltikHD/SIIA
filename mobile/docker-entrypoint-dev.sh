#!/bin/bash

# Script de inicialização para desenvolvimento mobile
# Inclui debugging capabilities

echo "=== Iniciando SIA2 Mobile Development Container ==="

# Inicia Xvfb (X Virtual Framebuffer) para execução headless
echo "Iniciando Xvfb..."
Xvfb :99 -screen 0 1024x768x24 &

# Aguarda o Xvfb inicializar
sleep 3

# Verifica se o Xvfb está rodando
if pgrep -x "Xvfb" > /dev/null; then
    echo "Xvfb iniciado com sucesso"
else
    echo "Erro ao iniciar Xvfb"
fi

# Exibe variáveis de ambiente para debug
echo "=== Variáveis de ambiente ==="
echo "DISPLAY: $DISPLAY"
echo "KIVY_WINDOW: $KIVY_WINDOW"
echo "KIVY_GL_BACKEND: $KIVY_GL_BACKEND"
echo "KIVY_LOG_LEVEL: $KIVY_LOG_LEVEL"

# Executa o comando passado como argumento
echo "=== Executando aplicação ==="
exec "$@"
