Write-Host "=== Setup KPIs Torre de Controle ===" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Python Backend
Write-Host "`n[Backend] Verificando Python..." -ForegroundColor Green
if (-not (Test-Path "backend\venv")) {
    Write-Host "   Criando virtual environment..."
    python -m venv backend\venv
}

Write-Host "   Instalando dependências Python..."
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt --quiet

# Node Frontend
Write-Host "`n[Frontend] Instalando dependências Node..." -ForegroundColor Green
if (-not (Test-Path "frontend\node_modules")) {
    npm install --prefix frontend
}

# Build Frontend (produção)
Write-Host "`n[Frontend] Buildando para produção..." -ForegroundColor Yellow
npm run build --prefix frontend

Write-Host "`n=== Setup concluído! ===" -ForegroundColor Green
Write-Host "Execute: .\run.ps1" -ForegroundColor White