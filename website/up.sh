#!/usr/bin/env bash
set -e

echo "🚀 Subindo SIIA (web + db)"
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker não encontrado"; exit 1;
fi

if [ ! -f .env ]; then
  echo "⚠️  .env ausente; usando .env.example como base";
  cp .env.example .env || true
fi

docker compose up -d --build
echo "✅ Pronto em http://localhost:5000"
