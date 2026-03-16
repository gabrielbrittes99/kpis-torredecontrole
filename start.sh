#!/bin/bash
# ============================================
# KPIs Torre de Controle — Start Script
# Sobe backend (FastAPI) e frontend (Vue/Vite)
# ============================================

set -e

echo "🚀 Iniciando KPIs Torre de Controle..."
echo ""

# Limpa processos anteriores para evitar conflito de porta
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

# --- Backend ---
echo "📦 Configurando Backend..."
cd backend

if [ ! -d ".venv" ]; then
    echo "   Criando ambiente virtual Python..."
    python3 -m venv .venv
fi

echo "   Ativando venv e instalando dependências..."
source .venv/bin/activate
pip install -r requirements.txt --quiet

echo "   ✅ Backend pronto!"
echo "   Iniciando servidor na porta 8000..."
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

cd ..

# --- Frontend ---
echo ""
echo "📦 Configurando Frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "   Instalando dependências npm..."
    npm install
fi

echo "   ✅ Frontend pronto!"
echo "   Iniciando dev server na porta 5173..."
npm run dev &
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
