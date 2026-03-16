#!/bin/bash
# Script de diagnóstico para carros "Outros"
cd "$(dirname "$0")"

echo "Rodando diagnóstico no ambiente do backend..."
cd backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 ../_diag_outros.py
