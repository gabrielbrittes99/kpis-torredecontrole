#!/bin/bash
set -e

echo "============================================"
echo "  Preparar projeto para Windows"
echo "============================================"
echo ""

# --- Build do frontend ---
echo "[...] Instalando dependencias do frontend..."
cd frontend
npm install --silent

echo "[...] Buildando frontend (npm run build)..."
npm run build

if [ ! -f "dist/index.html" ]; then
    echo "[ERRO] Build falhou! dist/index.html nao encontrado."
    exit 1
fi

echo "[OK] Frontend buildado com sucesso"
cd ..

# --- Resumo ---
echo ""
echo "============================================"
echo "  Pronto para zipar!"
echo "============================================"
echo ""
echo "O frontend foi buildado em frontend/dist/"
echo ""
echo "Proximo passo:"
echo "  1. Zipe o projeto inteiro"
echo "  2. Transfira para o Windows"
echo "  3. Duplo-clique em iniciar.bat"
echo ""
