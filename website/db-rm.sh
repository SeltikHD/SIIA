#!/bin/bash

# Script para remover containers e volumes do projeto SIA2
echo "=== LIMPEZA DO PROJETO SIA2 ==="

# Verifica se o Docker está rodando
if ! docker info >/dev/null 2>&1; then
    echo "❌ Erro: Docker não está rodando."
    exit 1
fi

echo "🛑 Parando e removendo todos os containers do projeto..."

# Para todos os serviços
docker compose down

# Remove também containers órfãos
docker compose down --remove-orphans

echo "🗑️  Removendo volumes do banco de dados..."

# Remove volumes específicos do projeto
docker compose down -v

# Remove volumes nomeados
docker volume rm sia2_postgres_data 2>/dev/null && echo "✅ Volume sia2_postgres_data removido" || echo "ℹ️  Volume sia2_postgres_data não encontrado"

# Opção para limpeza completa
read -p "Deseja também remover imagens Docker criadas para o projeto? [s/N]: " REMOVE_IMAGES
REMOVE_IMAGES=${REMOVE_IMAGES:-n}

if [[ $REMOVE_IMAGES =~ ^[Ss]$ ]]; then
    echo "🗑️  Removendo imagens do projeto..."
    
    # Remove imagens do projeto (se existirem)
    docker rmi website-web 2>/dev/null && echo "✅ Imagem website-web removida" || echo "ℹ️  Imagem website-web não encontrada"
    docker rmi mobile-mobile 2>/dev/null && echo "✅ Imagem mobile-mobile removida" || echo "ℹ️  Imagem mobile-mobile não encontrada"
    
    # Remove imagens não utilizadas
    docker image prune -f
fi

# Limpeza adicional (opcional)
read -p "Deseja realizar limpeza geral do Docker (containers, redes, imagens não utilizadas)? [s/N]: " DEEP_CLEAN
DEEP_CLEAN=${DEEP_CLEAN:-n}

if [[ $DEEP_CLEAN =~ ^[Ss]$ ]]; then
    echo "🧹 Realizando limpeza geral do Docker..."
    docker system prune -f
    echo "✅ Limpeza geral concluída"
fi

echo ""
echo "🎉 Limpeza do projeto SIA2 concluída!"
echo ""
echo "📋 Para reiniciar o projeto:"
echo "   ./db-init.sh  # Inicializar banco"
echo "   docker compose up  # Iniciar projeto completo"
