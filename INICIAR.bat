@echo off
chcp 65001 >nul 2>&1
title Torre de Controle - Gritsch

echo.
echo  ============================================
echo    Torre de Controle - Gritsch
echo  ============================================
echo.

:: ─────────────────────────────────────────────
:: 1. VERIFICAR PYTHON
:: ─────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRO] Python nao encontrado nesta maquina.
    echo.
    echo  Instale o Python 3.11 em:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANTE: durante a instalacao, marque a opcao
    echo  "Add Python to PATH" antes de clicar em Install.
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER% encontrado.

:: ─────────────────────────────────────────────
:: 2. VERIFICAR FRONTEND BUILDADO
:: ─────────────────────────────────────────────
if not exist "frontend\dist\index.html" (
    echo.
    echo  [ERRO] Frontend nao esta buildado.
    echo.
    echo  No computador de desenvolvimento, execute:
    echo    npm run build --prefix frontend
    echo.
    echo  Depois transfira a pasta completa do projeto
    echo  (incluindo frontend\dist) para esta maquina.
    pause
    exit /b 1
)
echo  [OK] Frontend buildado encontrado.

:: ─────────────────────────────────────────────
:: 3. VERIFICAR ARQUIVO .ENV
:: ─────────────────────────────────────────────
if not exist "backend\.env" (
    echo.
    echo  [ERRO] Arquivo de configuracao nao encontrado.
    echo.
    echo  Crie o arquivo backend\.env com as credenciais
    echo  do banco de dados antes de continuar.
    echo.
    echo  Exemplo de conteudo do .env:
    echo    DW_HOST=192.168.0.37
    echo    DW_PORT=5433
    echo    DW_DB=dw
    echo    DW_USER=...
    echo    DW_PASSWORD=...
    echo    RAILWAY_DB_URL=postgresql://...
    echo.
    pause
    exit /b 1
)
echo  [OK] Arquivo .env encontrado.

:: ─────────────────────────────────────────────
:: 4. CRIAR AMBIENTE VIRTUAL (primeira vez)
:: ─────────────────────────────────────────────
if not exist "backend\venv\Scripts\python.exe" (
    echo.
    echo  [...] Criando ambiente virtual Python...
    echo       (isso leva alguns segundos, apenas na primeira vez)
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo  [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo  [OK] Ambiente virtual criado.
)

:: ─────────────────────────────────────────────
:: 5. INSTALAR DEPENDENCIAS (primeira vez ou atualizacao)
:: ─────────────────────────────────────────────
backend\venv\Scripts\python.exe -c "import fastapi, uvicorn, pandas, sqlalchemy" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [...] Instalando dependencias Python...
    echo       (isso pode levar 1-3 minutos na primeira vez)
    backend\venv\Scripts\pip.exe install -r backend\requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo  [ERRO] Falha ao instalar dependencias.
        echo  Verifique se ha conexao com a internet.
        pause
        exit /b 1
    )
    echo  [OK] Dependencias instaladas.
) else (
    echo  [OK] Dependencias Python ja instaladas.
)

:: ─────────────────────────────────────────────
:: 6. INICIAR SERVIDOR EM JANELA SEPARADA
:: ─────────────────────────────────────────────
echo.
echo  [...] Iniciando servidor backend...

start "TorreDeControle-Servidor" /min cmd /c "cd backend && ..\backend\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000"

:: Aguardar o servidor subir
echo  [...] Aguardando servidor inicializar...
timeout /t 5 /nobreak >nul

:: Verificar se servidor respondeu
curl -s http://localhost:8000/api/sistema/health >nul 2>&1
if %errorlevel% neq 0 (
    :: Tenta mais 5 segundos
    timeout /t 5 /nobreak >nul
)

echo  [OK] Servidor rodando em http://localhost:8000

:: ─────────────────────────────────────────────
:: 7. ABRIR BROWSER EM MODO KIOSK (TV fullscreen)
:: ─────────────────────────────────────────────
echo.
echo  [...] Abrindo painel no navegador...

:: Tenta Microsoft Edge (padrao no Windows 10/11)
where msedge >nul 2>&1
if %errorlevel% equ 0 (
    start "" msedge --kiosk http://localhost:8000/transacoes --edge-kiosk-type=fullscreen --no-first-run --disable-popup-blocking
    goto :servidor_ok
)

:: Tenta Google Chrome
where chrome >nul 2>&1
if %errorlevel% equ 0 (
    start "" chrome --kiosk http://localhost:8000/transacoes --no-first-run --disable-popup-blocking
    goto :servidor_ok
)

:: Fallback: abre no navegador padrao (sem kiosk)
echo  [AVISO] Edge e Chrome nao encontrados. Abrindo no navegador padrao...
echo  Para modo fullscreen, pressione F11 no navegador.
start http://localhost:8000/transacoes

:servidor_ok
echo.
echo  ============================================
echo    Sistema rodando!
echo    http://localhost:8000/transacoes
echo.
echo    Para ENCERRAR: execute PARAR.bat
echo    ou feche esta janela + a janela do servidor
echo  ============================================
echo.
pause
