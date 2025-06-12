# Dockerfile para a aplicação mobile Kivy
FROM python:3.11-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para Kivy
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-dev \
    libgles2-mesa-dev \
    libgstreamer1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    libfreetype6-dev \
    xvfb \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Instala Kivy e dependências
RUN pip install --no-cache-dir kivy[base] kivymd requests

# Copia o código da aplicação
COPY . .

# Expõe porta para desenvolvimento
EXPOSE 8080

# Define variáveis de ambiente para execução headless
ENV KIVY_WINDOW=sdl2
ENV KIVY_GL_BACKEND=gl
ENV DISPLAY=:99

# Script de inicialização
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Comando padrão
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "main.py"]
