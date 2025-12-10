@echo off
setlocal ENABLEEXTENSIONS

REM ─────────────────────────────────────────────────────────────
REM  Del session  Telethon: %LOCALAPPDATA%\TelegramUserSender\my_account.session
REM  close exe for unblock file REM ─────────────────────────────────────────────────────────────

set "APPDIR=%LOCALAPPDATA%\TelegramUserSender"
set "BASE=%APPDIR%\my_account.session"

echo.
echo  ▶ DIR: "%APPDIR%"
echo  ▶ Session Base: "%BASE%"
echo.

REM 1) close programms for unblock session program 
for %%P in ("TelegramUserSender.exe" "main.exe") do (
    tasklist | find /I %%~P >NUL 2>&1
    if not errorlevel 1 (
        echo  ⏹ Закриваю %%~P ...
        taskkill /F /IM %%~P >NUL 2>&1
    )
)

REM 2) Del main file session SQLite
set "DELETED=0"
for %%F in ("%BASE%" "%BASE%-wal" "%BASE%-shm" "%BASE%-journal") do (
    if exist "%%~F" (
        del /F /Q "%%~F" >NUL 2>&1
        if not exist "%%~F" (
            echo  ✅ Видалено: %%~F
            set "DELETED=1"
        ) else (
            echo  ❌ not deleted: %%~F
        )
    )
)

if "%DELETED%"=="0" (
    echo  ℹ️ not found to del. files session not found.
) else (
    echo  ✔ ok. file session deleted !
)

echo.
echo  next run programm enter key  (and 2FA, if enable).
echo.
pause
endlocal
