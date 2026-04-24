@echo off
chcp 65001 >nul 2>&1
title Torre de Controle - KPIs Gritsch

echo ============================================
echo   Torre de Controle - KPIs Gritsch
echo ============================================
echo.

REM --- Verificar Python ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Instale o Python 3.10+ em: https://www.python.org/downloads/
    echo IMPORTANTE: Marque "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version

REM --- Verificar frontend buildado ---
if not exist "frontend\dist\index.html" (
    echo.
    echo [ERRO] Frontend nao esta buildado!
    echo O arquivo frontend\dist\index.html nao foi encontrado.
    echo.
    echo No Linux, rode: ./preparar.sh
    echo Depois zipe o projeto novamente e transfira.
    echo.
    pause
    exit /b 1
)

echo [OK] Frontend buildado encontrado

REM --- Criar venv se nao existe ---
if not exist "backend\venv\Scripts\python.exe" (
    echo.
    echo [...] Criando ambiente virtual Python...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado
)

REM --- Instalar dependencias ---
echo.
echo [...] Instalando dependencias Python...
backend\venv\Scripts\pip install -r backend\requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias.
    echo Verifique o arquivo backend\requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas

REM --- Abrir navegador apos 3 segundos ---
echo.
echo [...] Abrindo navegador em 3 segundos...
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

REM --- Iniciar servidor ---
echo.
echo ============================================
echo   Servidor iniciando em http://localhost:8000
echo   Pressione Ctrl+C para parar
echo ============================================
echo.

cd backend
..\backend\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000
cd ..

echo.
echo Servidor encerrado.
pause
