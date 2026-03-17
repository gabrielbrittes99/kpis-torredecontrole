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

echo "   Instalando/Verificando dependências..."
pip install -r requirements.txt --quiet

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
# Usamos o preview do vite para servir o build de produção ou o dev server com host
# Se for produção real, o ideal seria um servidor estático, mas para subir rápido:
npm run dev -- --host 0.0.0.0 &
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
