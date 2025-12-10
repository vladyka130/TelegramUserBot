@echo off
setlocal
cd /d "%~dp0"

if not exist "emojis" mkdir "emojis"

python -m pip show telethon >NUL 2>&1
if errorlevel 1 (
  echo ❌ В цьому середовищі нема Telethon. Активуй той самий venv, де все працює в PyCharm.
  pause & exit /b 1
)

python -m PyInstaller --noconfirm --windowed --onedir ^
  --name "TelegramUserSender" ^
  --collect-submodules telethon ^
  --hidden-import pyaes --hidden-import rsa --hidden-import certifi ^
  --add-data "emojis;emojis" ^
  telegram_my_dpi.py

echo.
echo ✅ GOOD: dist\TelegramUserSender\TelegramUserSender.exe
echo.
pause
endlocal