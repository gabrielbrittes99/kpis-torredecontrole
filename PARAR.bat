@echo off
chcp 65001 >nul 2>&1
title Encerrando Torre de Controle

echo.
echo  Encerrando Torre de Controle...

:: Fecha janela do servidor pelo titulo
taskkill /FI "WINDOWTITLE eq TorreDeControle-Servidor*" /F >nul 2>&1

:: Mata processo uvicorn se ainda estiver rodando
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8000 "') do (
    taskkill /PID %%p /F >nul 2>&1
)

echo  [OK] Servidor encerrado.
echo.
timeout /t 2 /nobreak >nul
