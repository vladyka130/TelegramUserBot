@echo off
echo ============================================
echo Запуск Telegram User Bot (Kivy версія)
echo ============================================
echo.

REM Перевірка чи встановлено Kivy
python -c "import kivy" 2>nul
if %errorlevel% neq 0 (
    echo [ПОМИЛКА] Kivy не встановлено!
    echo.
    echo Встановіть залежності:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Запуск додатка
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ПОМИЛКА] Не вдалося запустити додаток
    echo.
    pause
)

