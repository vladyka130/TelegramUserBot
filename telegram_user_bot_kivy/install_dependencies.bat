@echo off
echo ============================================
echo Встановлення залежностей для Kivy версії
echo ============================================
echo.

echo [1/3] Встановлення Kivy...
pip install kivy>=2.1.0
if %errorlevel% neq 0 (
    echo [ПОМИЛКА] Не вдалося встановити Kivy
    pause
    exit /b 1
)

echo.
echo [2/3] Встановлення Telethon...
pip install telethon>=1.28.0
if %errorlevel% neq 0 (
    echo [ПОМИЛКА] Не вдалося встановити Telethon
    pause
    exit /b 1
)

echo.
echo [3/3] Встановлення certifi...
pip install certifi
if %errorlevel% neq 0 (
    echo [ПОМИЛКА] Не вдалося встановити certifi
    pause
    exit /b 1
)

echo.
echo ============================================
echo [УСПІХ] Всі залежності встановлено!
echo ============================================
echo.
echo Тепер можна запустити:
echo   python main.py
echo.
pause




