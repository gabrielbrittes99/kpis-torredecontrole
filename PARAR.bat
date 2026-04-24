@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Encerrando Torre de Controle - Gritsch

echo.
echo  ============================================================
echo    Encerrando Torre de Controle...
echo  ============================================================
echo.

:: 1. Fecha janela do servidor pelo titulo
echo  [...] Fechando janelas do servidor...
taskkill /FI "WINDOWTITLE eq TorreDeControle-Servidor*" /F >nul 2>&1

:: 2. Mata processo na porta 8000 (Uvicorn)
echo  [...] Liberando porta 8000...
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8000 "') do (
    taskkill /PID %%p /F >nul 2>&1
)

:: 3. Mata processos Python remanescentes no venv (opcional, mas seguro)
echo  [...] Finalizando processos Python...
taskkill /IM python.exe /F /FI "MODULES eq *backend\venv*" >nul 2>&1

:: 4. Opcional: Fechar navegadores em modo Kiosk?
:: Normalmente nao queremos fechar o navegador se o usuario estiver usando para outra coisa,
:: mas se for uma TV dedicada, pode ser util.
:: taskkill /IM msedge.exe /F >nul 2>&1
:: taskkill /IM chrome.exe /F >nul 2>&1

echo.
echo  [OK] Sistema encerrado com sucesso.
echo.
timeout /t 3 /nobreak >nul
exit /b 0
