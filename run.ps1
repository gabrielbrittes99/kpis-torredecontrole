Write-Host "=== KPIs Torre de Controle (Produção) ===" -ForegroundColor Cyan
Write-Host "Acesse: http://localhost:8000" -ForegroundColor Green

cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000