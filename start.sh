#!/bin/bash
# ============================================
# KPIs Torre de Controle — Start Script
# Railway: só sobe o backend (FastAPI serve o frontend via StaticFiles)
# Local:   sobe backend + vite dev server
# ============================================

set -e

echo "Iniciando KPIs Torre de Controle..."
echo "Rodando em: $(date)"
echo ""

# Limpa processos anteriores
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# --- Backend ---
echo "Configurando Backend..."
cd backend

if [ -z "$RAILWAY_ENVIRONMENT" ] && [ -z "$RAILWAY_SERVICE_NAME" ]; then
  # Local: usa venv
  if [ ! -d "venv" ]; then
    echo "   Criando virtual environment..."
    python3 -m venv venv || python -m venv venv
  fi
  source venv/bin/activate
  pip install -r requirements.txt --quiet
fi

echo "   Iniciando servidor na porta ${PORT:-8000}..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &
BACKEND_PID=$!

cd ..

# --- Frontend (apenas local) ---
if [ -z "$RAILWAY_ENVIRONMENT" ] && [ -z "$RAILWAY_SERVICE_NAME" ]; then
  echo ""
  echo "Configurando Frontend (dev)..."
  cd frontend
  ./node_modules/.bin/vite --host 0.0.0.0 &
  FRONTEND_PID=$!
  cd ..
  echo "   Frontend: http://localhost:5173"
else
  FRONTEND_PID=""
  echo "   Railway: frontend servido pelo FastAPI em /dist"
fi

echo ""
echo "============================================"
echo "Backend API:  http://localhost:${PORT:-8000}"
echo "Swagger Docs: http://localhost:${PORT:-8000}/docs"
echo "============================================"

trap "kill $BACKEND_PID ${FRONTEND_PID:-} 2>/dev/null; exit 0" SIGINT SIGTERM
wait $BACKEND_PID
