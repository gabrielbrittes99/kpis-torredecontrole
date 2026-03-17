#!/bin/bash
# ============================================
# KPIs Torre de Controle — Start Script
# Sobe backend (FastAPI) e frontend (Vue/Vite)
# ============================================

set -e

echo "🚀 Iniciando KPIs Torre de Controle (v2 - Railway Auto-Config)..."
echo "📅 Rodando em: $(date)"
echo ""

# Limpa processos anteriores para evitar conflito de porta
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# --- Backend ---
echo "📦 Configurando Backend..."
cd backend

# Detecta ambiente: Railway já instala deps no build phase via nixpacks.toml
if [ -z "$RAILWAY_ENVIRONMENT" ] && [ -z "$RAILWAY_SERVICE_NAME" ]; then
  # Local: usa venv para não conflitar com pacotes do sistema
  if [ ! -d "venv" ]; then
    echo "   Criando virtual environment..."
    python3 -m venv venv
  fi
  source venv/bin/activate
  pip install -r requirements.txt --quiet
fi

echo "   ✅ Backend pronto!"
echo "   Iniciando servidor na porta 8000..."
# No Railway, a porta é passada pela variável PORT
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} &
BACKEND_PID=$!

cd ..

# --- Frontend ---
echo ""
echo "📦 Configurando Frontend..."
cd frontend

echo "   ✅ Frontend pronto!"
if [ -n "$RAILWAY_ENVIRONMENT" ] || [ -n "$RAILWAY_SERVICE_NAME" ]; then
  # Railway: serve o build de produção gerado no build phase
  npm run preview -- --host 0.0.0.0 --port ${FRONTEND_PORT:-4173} &
else
  # Local: dev server com hot reload
  npm run dev -- --host 0.0.0.0 &
fi
FRONTEND_PID=$!

cd ..

# --- Info ---
echo ""
echo "============================================"
echo "🎯 Tudo rodando!"
echo ""
echo "   🔧 Backend API:   http://localhost:8000"
echo "   📊 Swagger Docs:  http://localhost:8000/docs"
echo "   🖥️  Frontend:      http://localhost:5173"
echo ""
echo "   Pressione Ctrl+C para parar tudo."
echo "============================================"

# Espera e mata ambos ao sair
trap "echo ''; echo '🛑 Parando...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
