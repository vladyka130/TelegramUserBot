@echo off
echo ============================================
echo Збірка APK через Buildozer
echo ============================================
echo.

REM Перевірка WSL
wsl --list --verbose >nul 2>&1
if %errorlevel% neq 0 (
    echo [ПОМИЛКА] WSL не встановлений!
    echo.
    echo Buildozer на Windows потребує WSL2.
    echo Встановіть WSL2:
    echo   1. Відкрийте PowerShell як Адміністратор
    echo   2. Виконайте: wsl --install
    echo   3. Перезавантажте комп'ютер
    echo.
    pause
    exit /b 1
)

echo [OK] WSL знайдено
echo.

REM Перевірка чи є buildozer.spec
if not exist "buildozer.spec" (
    echo [ПОМИЛКА] buildozer.spec не знайдено!
    echo Запустіть скрипт з папки telegram_user_bot_kivy
    pause
    exit /b 1
)

echo [OK] buildozer.spec знайдено
echo.

REM Отримуємо абсолютний шлях до поточної папки
for %%I in (.) do set CURRENT_DIR=%%~fI

echo [ІНФО] Поточна папка: %CURRENT_DIR%
echo.
echo [1/3] Встановлення buildozer у WSL (якщо потрібно)...
echo.

REM Встановлюємо buildozer у WSL
wsl bash -c "cd /mnt/d/'Python MY EXE'/'TelegramUserBot'/telegram_user_bot_kivy && pip3 install --user buildozer 2>&1 || echo 'Buildozer вже встановлений або помилка встановлення'"

echo.
echo [2/3] Встановлення системних залежностей у WSL...
echo.

REM Встановлюємо системні залежності (тільки якщо потрібно)
wsl bash -c "sudo apt-get update && sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev 2>&1 | head -20"

echo.
echo [3/3] Збірка APK (це займе 20-30 хвилин при першій збірці)...
echo.

REM Конвертуємо Windows шлях до WSL шляху
set WSL_PATH=%CURRENT_DIR%
set WSL_PATH=%WSL_PATH:D:\=/mnt/d/%
set WSL_PATH=%WSL_PATH:\=/%
set WSL_PATH=%WSL_PATH: =%%20%

echo Виконую buildozer android debug...
echo Це може зайняти багато часу...
echo.

REM Запускаємо buildozer через WSL
wsl bash -c "cd '%WSL_PATH%' && export PATH=$PATH:~/.local/bin && buildozer android debug"

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo [УСПІХ] APK зібрано!
    echo ============================================
    echo.
    echo APK файл знаходиться тут:
    echo bin/telegramuserbot-*.apk
    echo.
    echo Розмір файлу:
    if exist "bin\*.apk" (
        dir /s /b bin\*.apk
    )
    echo.
    echo Для встановлення на телефон:
    echo 1. Скопіюйте APK на телефон
    echo 2. Увімкніть "Джерела невідомого походження"
    echo 3. Відкрийте APK файл на телефоні
    echo.
) else (
    echo.
    echo ============================================
    echo [ПОМИЛКА] Не вдалося зібрати APK
    echo ============================================
    echo.
    echo Можливі причини:
    echo - Android SDK/NDK не встановлені (buildozer завантажить автоматично)
    echo - Проблеми з залежностями
    echo - Помилки в коді
    echo.
    echo Спробуйте:
    echo wsl bash -c "cd '%WSL_PATH%' && buildozer android clean"
    echo wsl bash -c "cd '%WSL_PATH%' && buildozer android debug"
    echo.
)

pause




