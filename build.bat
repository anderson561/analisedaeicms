@echo off
setlocal enabledelayedexpansion

set VENV_PYTHON=%~dp0.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo [ERRO] Ambiente virtual nao encontrado em .venv\
    echo Rode primeiro:
    echo     python -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

if "%TESSERACT_HOME%"=="" set TESSERACT_HOME=C:\Program Files\Tesseract-OCR
set VENDOR_TESSERACT=%~dp0vendor\tesseract

if not exist "%VENDOR_TESSERACT%\tesseract.exe" (
    echo Preparando pacote minimo do Tesseract em vendor\tesseract\...

    if not exist "%TESSERACT_HOME%\tesseract.exe" (
        echo [ERRO] Tesseract nao encontrado em "%TESSERACT_HOME%"
        echo Instale o Tesseract-OCR ou defina a variavel TESSERACT_HOME apontando para a instalacao.
        pause
        exit /b 1
    )

    mkdir "%VENDOR_TESSERACT%\tessdata" 2>nul
    copy /y "%TESSERACT_HOME%\tesseract.exe" "%VENDOR_TESSERACT%\" >nul

    rem Copia TODAS as DLLs da instalacao (nao apenas um subconjunto escolhido a mao):
    rem testado isoladamente (PATH sem a instalacao do sistema) e confirmado que um
    rem subconjunto menor de DLLs falha com "DLL nao encontrada" em tempo de execucao.
    copy /y "%TESSERACT_HOME%\*.dll" "%VENDOR_TESSERACT%\" >nul

    copy /y "%TESSERACT_HOME%\tessdata\por.traineddata" "%VENDOR_TESSERACT%\tessdata\" >nul

    echo Pacote do Tesseract preparado.
    echo.
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
