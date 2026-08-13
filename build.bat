@echo off
setlocal

set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [ERRO] Ambiente virtual nao encontrado em .venv\
    echo Rode primeiro:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Gerando executavel do AuditaDAE...
echo.
"%VENV_PYTHON%" -m PyInstaller "%~dp0auditadae.spec" --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao gerar o executavel. Veja as mensagens acima.
    pause
    exit /b 1
)

echo.
echo Build concluido com sucesso!
echo Executavel atualizado em: %~dp0dist\AuditaDAE\AuditaDAE.exe
pause
