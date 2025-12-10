@echo off
chcp 65001 >nul
echo ============================================
echo  Налаштування WSL для збірки APK
echo ============================================
echo.
echo Цей скрипт налаштує WSL для роботи з Buildozer
echo.

REM Перевірка WSL
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] WSL не встановлено!
    echo.
    echo Спочатку встановіть WSL:
    echo   1. Запустіть install_wsl.bat як адміністратор
    echo   2. Або вручну: wsl --install (в PowerShell як адміністратор)
    echo   3. Перезавантажте комп'ютер
    echo.
    pause
    exit /b 1
)

echo [OK] WSL знайдено
echo.

REM Отримуємо поточний шлях Windows і конвертуємо в WSL формат
set CURRENT_WIN=%CD%

REM Використовуємо wslpath якщо доступно, інакше конвертуємо вручну
wsl wslpath -a "%CURRENT_WIN%" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%p in ('wsl wslpath -a "%CURRENT_WIN%"') do set WSL_PATH=%%p
) else (
    REM Ручна конвертація якщо wslpath недоступний
    set WSL_PATH=%CURRENT_WIN%
    set WSL_PATH=%WSL_PATH:D:\=/mnt/d/%
    set WSL_PATH=%WSL_PATH:C:\=/mnt/c/%
    set WSL_PATH=%WSL_PATH:\=/%
    set WSL_PATH=%WSL_PATH: =\\ %
    set WSL_PATH=%WSL_PATH://=/%
)

echo Windows шлях: %CURRENT_WIN%
echo WSL шлях: %WSL_PATH%
echo.

echo ============================================
echo  КРОК 1: Оновлення системи
echo ============================================
echo.

wsl bash -c "sudo apt-get update -qq && echo '[OK] Система оновлена' || echo '[!] Помилка оновлення'"

echo.
echo ============================================
echo  КРОК 2: Встановлення системних залежностей
echo ============================================
echo [ІНФО] Це може зайняти 5-10 хвилин...
echo.

wsl bash -c "sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev 2>&1 | grep -E '(встановлюється|вже|найновіший|OK|ERROR)' || echo '[OK] Залежності встановлено'"

echo.
echo ============================================
echo  КРОК 3: Встановлення Buildozer
echo ============================================
echo.

wsl bash -c "if command -v buildozer >/dev/null 2>&1; then echo '[OK] Buildozer вже встановлено'; else echo '[ІНФО] Встановлюю Buildozer...'; pip3 install --user buildozer && echo '[OK] Buildozer встановлено' || echo '[X] Помилка встановлення Buildozer'; fi"

echo.
echo ============================================
echo  КРОК 4: Налаштування PATH
echo ============================================
echo.

wsl bash -c "if grep -q '.local/bin' ~/.bashrc 2>/dev/null; then echo '[OK] PATH вже налаштовано'; else echo 'export PATH=\$PATH:~/.local/bin' >> ~/.bashrc && echo '[OK] PATH додано до .bashrc'; fi"

echo.
echo ============================================
echo  КРОК 5: Перевірка встановлення
echo ============================================
echo.

wsl bash -c "export PATH=\$PATH:~/.local/bin && if command -v buildozer >/dev/null 2>&1; then echo '[OK] Buildozer доступний'; buildozer --version 2>&1 | head -1; else echo '[X] Buildozer не знайдено. Спробуйте встановити вручну:'; echo '    wsl'; echo '    pip3 install --user buildozer'; echo '    export PATH=\$PATH:~/.local/bin'; fi"

echo.
echo ============================================
echo  Налаштування завершено!
echo ============================================
echo.
echo Тепер можна запускати build_apk_simple.bat для збірки APK
echo.
echo Для ручної перевірки введіть:
echo   wsl
echo   export PATH=\$PATH:~/.local/bin
echo   buildozer --version
echo.

pause

