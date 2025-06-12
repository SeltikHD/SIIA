#!/bin/bash

# Script de inicialização para o container mobile
# Inicia um display virtual para aplicações GUI

# Inicia Xvfb (X Virtual Framebuffer) para execução headless
Xvfb :99 -screen 0 1024x768x24 &

# Aguarda o Xvfb inicializar
sleep 2

# Executa o comando passado como argumento
exec "$@"
