Write-Host "Iniciando KPIs Torre de Controle (PowerShell)..." -ForegroundColor Cyan

# 1. Parar processos antigos (se houver)
Write-Host "Limpando processos antigos..." -ForegroundColor Yellow
$processes = Get-Process | Where-Object { $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*vite*" }
foreach ($p in $processes) {
    try {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Write-Host "   Parado processo: $($p.Id)"
    } catch {}
}

# 2. Configurar Backend
Write-Host "`n[Backend] Configurando..." -ForegroundColor Green
cd backend

if (-not (Test-Path "venv")) {
    Write-Host "   Criando virtual environment..."
    python -m venv venv
}

Write-Host "   Instalando dependências..."
.\venv\Scripts\python.exe -m pip install -r requirements.txt --quiet uvicorn

Write-Host "   Iniciando Backend na porta 8000 (segundo plano)..."
Start-Process powershell -ArgumentList "-NoProfile -Command .\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000" -WindowStyle Minimized

# 3. Configurar Frontend
Write-Host "`n[Frontend] Configurando..." -ForegroundColor Green
cd ..\frontend

Write-Host "   Instalando dependências (se necessário)..."
npm install --quiet

Write-Host "   Iniciando Frontend (Vite)..." -ForegroundColor White
Write-Host "   Acesse: http://localhost:5173" -ForegroundColor Green
npm run dev
