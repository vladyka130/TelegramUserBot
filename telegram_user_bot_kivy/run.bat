@echo off
echo ============================================
echo Запуск Telegram User Bot (Kivy версія)
echo ============================================
echo.

REM Спробувати використати venv якщо є
if exist "..\Grafik_venv\Scripts\activate.bat" (
    echo [OK] Використовується venv: Grafik_venv
    call ..\Grafik_venv\Scripts\activate.bat
    python main.py
) else (
    echo [OK] Використовується глобальне середовище Python
    python main.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ПОМИЛКА] Не вдалося запустити додаток
    echo.
    echo Можливі причини:
    echo - Не встановлено Kivy: pip install kivy
    echo - Не встановлено Telethon: pip install telethon
    echo.
    echo Спробуйте виконати: setup_venv.bat
    echo.
    pause
)




