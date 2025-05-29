#!/bin/bash

CONTAINER_NAME=postgres-container
VOLUME_NAME=pgdata

echo "Removendo container e volume PostgreSQL..."

# Para e remove o container, se existir
podman rm -f $CONTAINER_NAME 2>/dev/null || echo "Container não encontrado."

# Remove o volume, se existir
podman volume rm $VOLUME_NAME 2>/dev/null || echo "Volume não encontrado."

echo "Tudo removido."
