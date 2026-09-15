@echo off
setlocal enabledelayedexpansion

set "INSTALL_DIR=%~1"
set "STAGING_NOVO=%~2"
set "PID_ANTIGO=%~3"

if "%INSTALL_DIR%"=="" goto :erro_args
if "%STAGING_NOVO%"=="" goto :erro_args
if "%PID_ANTIGO%"=="" goto :erro_args

set "BACKUP_DIR=%INSTALL_DIR%_old"

rem Espera o processo antigo encerrar (timeout de 60s, checagem a cada 1s).
set /a TENTATIVAS=0
:espera_pid
tasklist /fi "PID eq %PID_ANTIGO%" 2>nul | find "%PID_ANTIGO%" >nul
if not errorlevel 1 (
    set /a TENTATIVAS+=1
    if !TENTATIVAS! geq 60 goto :erro_timeout
    timeout /t 1 /nobreak >nul
    goto :espera_pid
)

rem Renomeia a instalacao atual para backup (rename, mesmo volume = quase instantaneo).
if exist "%BACKUP_DIR%" rmdir /s /q "%BACKUP_DIR%"
move /y "%INSTALL_DIR%" "%BACKUP_DIR%" >nul
if errorlevel 1 goto :erro_move_backup

rem Move a nova versao para o lugar da instalacao.
move /y "%STAGING_NOVO%" "%INSTALL_DIR%" >nul
if errorlevel 1 goto :erro_move_novo

start "" "%INSTALL_DIR%\AuditaDAE.exe"
goto :limpeza

:erro_move_novo
rem Rollback: restaura o backup para o lugar original.
move /y "%BACKUP_DIR%" "%INSTALL_DIR%" >nul
start "" "%INSTALL_DIR%\AuditaDAE.exe"
goto :limpeza

:erro_move_backup
:erro_timeout
:erro_args
:limpeza
rem Autodeleta este script e a pasta de staging (pai), sem apagar o backup _old
rem (isso fica a cargo do proprio app no proximo start bem-sucedido).
(goto) 2>nul & del "%~f0"
