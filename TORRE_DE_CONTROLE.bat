@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1
title Torre de Controle - Gritsch
cd /d "%~dp0"

:: Cores para o terminal (apenas se suportado, mas o echo com ANSI pode falhar em alguns CMDs)
:: Vamos usar prefixos simples [OK], [ERRO], [AVISO]

echo.
echo  ============================================================
echo    TORRE DE CONTROLE - GRITSCH (Auto-Launcher)
echo  ============================================================
echo.

:: 1. VERIFICAR PRIVILEGIOS (Opcional, mas util para instalacoes)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo  [OK] Executando com privilegios de administrador.
) else (
    echo  [AVISO] Executando sem privilegios de administrador.
    echo          Se falhar ao instalar Python/Node, tente "Executar como Administrador".
)

:: 2. LOCALIZAR PYTHON
echo  [...] Procurando Python...
set "PYTHON_EXE="

:: Tentativa 1: Comando 'python'
where python >nul 2>&1
if !errorlevel! equ 0 (
    for /f "delims=" %%p in ('where python') do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%p"
    )
)

:: Tentativa 2: Comando 'python3'
if not defined PYTHON_EXE (
    where python3 >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%p in ('where python3') do (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%p"
        )
    )
)

:: Tentativa 3: Caminhos comuns
if not defined PYTHON_EXE (
    for %%d in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
        "C:\Program Files\Python312\python.exe"
        "C:\Program Files\Python311\python.exe"
        "C:\Program Files\Python310\python.exe"
        "C:\Python312\python.exe"
        "C:\Python311\python.exe"
    ) do (
        if exist "%%~d" if not defined PYTHON_EXE set "PYTHON_EXE=%%~d"
    )
)

if defined PYTHON_EXE (
    echo  [OK] Python encontrado: !PYTHON_EXE!
    goto :python_ok
)

:: Auto-Instalacao Python
echo  [AVISO] Python nao encontrado. Iniciando instalacao automatica...
where winget >nul 2>&1
if !errorlevel! equ 0 (
    echo  [...] Instalando Python 3.11 via winget...
    winget install --id Python.Python.3.11 --silent --accept-source-agreements --accept-package-agreements
    if !errorlevel! equ 0 goto :find_python_after_install
)

echo  [...] Baixando instalador oficial do Python 3.11...
set "PYINST=%TEMP%\python-installer.exe"
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%PYINST%' -UseBasicParsing } catch { exit 1 }"
if !errorlevel! neq 0 (
    echo  [ERRO] Falha ao baixar o Python. Verifique sua internet.
    pause
    exit /b 1
)
echo  [...] Instalando silenciosamente (isso pode demorar)...
"%PYINST%" /quiet InstallAllUsers=1 PrependPath=1
del /f /q "%PYINST%" >nul 2>&1

:find_python_after_install
:: Tenta localizar novamente
for %%d in ("C:\Program Files\Python311\python.exe" "C:\Program Files (x86)\Python311\python.exe" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe") do (
    if exist "%%~d" set "PYTHON_EXE=%%~d"
)
if not defined PYTHON_EXE (
    echo  [ERRO] Python foi instalado mas ainda nao foi localizado.
    echo         Por favor, instale o Python 3.11 manualmente e tente novamente.
    pause
    exit /b 1
)

:python_ok

:: 3. VERIFICAR .ENV
if not exist "backend\.env" (
    echo  [ERRO] Arquivo backend\.env nao encontrado!
    echo         Crie este arquivo com as credenciais do banco para continuar.
    if exist "backend\.env.example" (
        echo         Dica: Use o arquivo backend\.env.example como base.
    )
    pause
    exit /b 1
)

:: 4. AMBIENTE VIRTUAL E DEPENDENCIAS BACKEND
echo  [...] Verificando ambiente virtual (venv)...
if not exist "backend\venv\Scripts\python.exe" (
    echo  [...] Criando venv em backend\venv...
    "!PYTHON_EXE!" -m venv backend\venv
    if !errorlevel! neq 0 (
        echo  [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
)

echo  [...] Verificando/Instalando dependencias Python...
backend\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
backend\venv\Scripts\pip.exe install -r backend\requirements.txt --quiet
if !errorlevel! neq 0 (
    echo  [ERRO] Falha ao instalar dependencias do backend.
    pause
    exit /b 1
)
echo  [OK] Backend pronto.

:: 5. VERIFICAR FRONTEND (BUILD)
if not exist "frontend\dist\index.html" (
    echo  [AVISO] Frontend nao buildado. Procurando Node.js...
    set "NPM_CMD="
    where npm >nul 2>&1
    if !errorlevel! equ 0 ( set "NPM_CMD=npm" ) else (
        if exist "C:\Program Files\nodejs\npm.cmd" (set "NPM_CMD=C:\Program Files\nodejs\npm.cmd")
    )

    if not defined NPM_CMD (
        echo  [...] Node.js nao encontrado. Instalando via winget...
        winget install --id OpenJS.NodeJS.LTS --silent --accept-source-agreements --accept-package-agreements
        if exist "C:\Program Files\nodejs\npm.cmd" set "NPM_CMD=C:\Program Files\nodejs\npm.cmd"
    )

    if not defined NPM_CMD (
        echo  [ERRO] Node.js e necessario para buildar o frontend.
        echo         Por favor, instale o Node.js LTS e tente novamente.
        pause
        exit /b 1
    )

    echo  [...] Instalando dependencias do frontend (isso pode demorar)...
    pushd frontend
    call "!NPM_CMD!" install --silent
    echo  [...] Buildando frontend...
    call "!NPM_CMD!" run build
    popd
)
echo  [OK] Frontend pronto.

:: 6. LIMPEZA DE PROCESSOS ANTIGOS
echo  [...] Limpando sessoes anteriores na porta 8000...
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)

:: 7. INICIAR SERVIDOR
echo  [...] Iniciando servidor em segundo plano...
:: Usamos um arquivo de log para diagnosticos
set "LOG_FILE=%~dp0server_log.txt"
echo Servidor iniciado em %DATE% %TIME% > "%LOG_FILE%"
start "TorreDeControle-Servidor" /min cmd /c "cd /d "%~dp0backend" && "%~dp0backend\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 >> "%LOG_FILE%" 2>&1"

:: 8. AGUARDAR INICIALIZACAO
echo  [...] Aguardando o servidor responder (localhost:8000)...
set /a timeout_counter=0
:wait_loop
set /a timeout_counter+=1
timeout /t 2 /nobreak >nul
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>&1
if !errorlevel! neq 0 (
    if !timeout_counter! lss 20 (
        echo      - Tentativa !timeout_counter!/20...
        goto :wait_loop
    )
    echo  [AVISO] O servidor esta demorando mais que o esperado. Tentando abrir o navegador assim mesmo.
) else (
    echo  [OK] Servidor online!
)

:: 9. ABRIR NAVEGADOR (MODO KIOSK)
echo  [...] Abrindo painel em modo Fullscreen...
set "TARGET_URL=http://localhost:8000/transacoes"

where msedge >nul 2>&1
if !errorlevel! equ 0 (
    start "" msedge --kiosk "!TARGET_URL!" --edge-kiosk-type=fullscreen --no-first-run --disable-popup-blocking --disable-features=TranslateUI
    goto :finish
)

where chrome >nul 2>&1
if !errorlevel! equ 0 (
    start "" chrome --kiosk "!TARGET_URL!" --no-first-run --disable-popup-blocking --disable-features=TranslateUI
    goto :finish
)

:: Fallback
start "" "!TARGET_URL!"

:finish
echo.
echo  ============================================================
echo    SISTEMA EM OPERACAO!
echo  ============================================================
echo    URL: !TARGET_URL!
echo    Log: server_log.txt
echo.
echo    Para parar tudo: Execute PARAR.bat ou feche as janelas.
echo  ============================================================
echo.
timeout /t 10 /nobreak >nul
exit /b 0
