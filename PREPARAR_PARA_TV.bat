@echo off
chcp 65001 >nul 2>&1
title Preparando pacote para TV

echo.
echo  ============================================
echo    Preparando projeto para a TV
echo    (execute no computador de desenvolvimento)
echo  ============================================
echo.

:: ─────────────────────────────────────────────
:: 1. VERIFICAR NODE.JS
:: ─────────────────────────────────────────────
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Node.js nao encontrado.
    echo  Instale em: https://nodejs.org/
    pause
    exit /b 1
)
for /f %%v in ('node --version') do set NODEVER=%%v
echo  [OK] Node.js %NODEVER% encontrado.

:: ─────────────────────────────────────────────
:: 2. INSTALAR DEPENDENCIAS FRONTEND
:: ─────────────────────────────────────────────
if not exist "frontend\node_modules" (
    echo.
    echo  [...] Instalando dependencias Node.js...
    npm install --prefix frontend
    if %errorlevel% neq 0 (
        echo  [ERRO] Falha ao instalar dependencias Node.js.
        pause
        exit /b 1
    )
)
echo  [OK] Dependencias Node.js prontas.

:: ─────────────────────────────────────────────
:: 3. BUILD DO FRONTEND
:: ─────────────────────────────────────────────
echo.
echo  [...] Buildando frontend para producao...
npm run build --prefix frontend
if %errorlevel% neq 0 (
    echo  [ERRO] Falha no build do frontend.
    pause
    exit /b 1
)
echo  [OK] Frontend buildado em frontend\dist\

:: ─────────────────────────────────────────────
:: 4. INSTRUCOES FINAIS
:: ─────────────────────────────────────────────
echo.
echo  ============================================
echo    Build concluido!
echo.
echo    Agora transfira a pasta do projeto para a
echo    maquina da TV. O que precisa estar presente:
echo.
echo      backend\          (todo o conteudo)
echo      frontend\dist\    (gerado agora)
echo      INICIAR.bat
echo      PARAR.bat
echo.
echo    Nao esqueca de copiar tambem o arquivo:
echo      backend\.env      (credenciais do banco)
echo.
echo    Na maquina da TV:
echo      1. Instale Python 3.11 (marcar Add to PATH)
echo      2. Execute INICIAR.bat
echo  ============================================
echo.
pause
