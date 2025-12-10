@echo off
chcp 65001 >nul
echo ============================================
echo  Встановлення WSL2 для збірки APK
echo ============================================
echo.

REM Перевірка прав адміністратора
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] ПОМИЛКА: Скрипт потрібно запускати як Адміністратор!
    echo.
    echo 1. Клацніть правою кнопкою на файл
    echo 2. Виберіть "Запустити від імені адміністратора"
    echo.
    pause
    exit /b 1
)

echo [OK] Права адміністратора підтверджено
echo.

REM Перевірка чи WSL вже встановлено
wsl --status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] WSL вже встановлено!
    echo.
    wsl --status
    echo.
    echo Встановлені дистрибутиви:
    wsl --list --verbose
    echo.
    echo Якщо WSL2 встановлено, можна продовжувати збірку APK.
    echo Якщо потрібно встановити Ubuntu або оновити до WSL2:
    echo   wsl --install -d Ubuntu
    echo   або
    echo   wsl --set-version Ubuntu 2
    echo.
    pause
    exit /b 0
)

echo [ІНФО] WSL не знайдено. Починаю встановлення...
echo.

REM Перевірка чи включена функція Virtual Machine Platform
echo [1/4] Перевірка функцій Windows...
dism.exe /online /get-featureinfo /featurename:VirtualMachinePlatform >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Не вдалося перевірити Virtual Machine Platform
    echo    Спробуємо встановити вручну...
)

echo [2/4] Включення необхідних функцій Windows...
echo    Це може зайняти кілька хвилин...
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

if %errorlevel% neq 0 (
    echo.
    echo [X] Помилка при включенні функцій Windows.
    echo.
    echo Спробуйте вручну:
    echo   1. Відкрийте "Увімкнення або вимкнення компонентів Windows"
    echo   2. Увімкніть "Підсистема Windows для Linux"
    echo   3. Увімкніть "Платформа віртуальної машини"
    echo   4. Перезавантажте комп'ютер
    echo.
    pause
    exit /b 1
)

echo [OK] Функції Windows включено
echo.

echo [3/4] Встановлення WSL (за замовчуванням Ubuntu)...
echo    Це завантажить Ubuntu з Microsoft Store...
wsl --install

if %errorlevel% neq 0 (
    echo.
    echo [!] Автоматичне встановлення не вдалося.
    echo.
    echo Спробуйте вручну через PowerShell (як адміністратор):
    echo   wsl --install
    echo   або
    echo   wsl --install -d Ubuntu
    echo.
    echo Після встановлення потрібно:
    echo   1. Перезавантажити комп'ютер
    echo   2. Запустити WSL (автоматично відкриється термінал)
    echo   3. Створити користувача Linux (логін та пароль)
    echo   4. Оновити систему: sudo apt update ^&^& sudo apt upgrade -y
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  [✓] Встановлення WSL завершено!
echo ============================================
echo.
echo [ВАЖЛИВО] Потрібно перезавантажити комп'ютер!
echo.
echo Після перезавантаження:
echo   1. WSL автоматично відкриється
echo   2. Створіть користувача Linux (логін та пароль)
echo   3. Запустіть скрипт setup_wsl_environment.bat для налаштування
echo      (або встановіть вручну: sudo apt update, pip3 install buildozer, тощо)
echo.
echo Для перевірки після перезавантаження:
echo   wsl --status
echo   wsl --list --verbose
echo.

choice /C YN /M "Перезавантажити комп'ютер зараз"
if %errorlevel% equ 1 (
    shutdown /r /t 10 /c "Перезавантаження для завершення встановлення WSL. Перезавантаження через 10 секунд..."
    echo.
    echo Комп'ютер перезавантажиться через 10 секунд.
    echo Для скасування: shutdown /a
    timeout /t 10
) else (
    echo.
    echo Перезавантажте комп'ютер вручну, коли будете готові.
)

pause



