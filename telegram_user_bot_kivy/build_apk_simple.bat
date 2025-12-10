@echo off
chcp 65001 >nul
echo ============================================
echo  Збірка APK для Telegram User Bot
echo ============================================
echo.

cd /d "%~dp0"

REM Перевірка buildozer.spec
if not exist "buildozer.spec" (
    echo [X] ПОМИЛКА: buildozer.spec не знайдено!
    echo     Переконайтеся, що ви запускаєте скрипт з папки telegram_user_bot_kivy
    pause
    exit /b 1
)

echo [OK] buildozer.spec знайдено
echo.

REM Перевірка WSL
wsl --status >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] WSL не знайдено!
    echo.
    echo Для збірки APK на Windows потрібен WSL2.
    echo.
    echo Автоматичне встановлення:
    echo   1. Запустіть install_wsl.bat як Адміністратор
    echo   2. Перезавантажте комп'ютер
    echo   3. Запустіть setup_wsl_environment.bat для налаштування
    echo   4. Потім запустіть цей скрипт знову
    echo.
    echo Або встановіть вручну:
    echo   1. Відкрийте PowerShell як Адміністратор
    echo   2. Виконайте: wsl --install
    echo   3. Перезавантажте комп'ютер
    echo   4. Запустіть setup_wsl_environment.bat
    echo.
    echo Швидке встановлення:
    choice /C YN /M "Запустити install_wsl.bat зараз (потрібні права адміністратора)"
    if %errorlevel% equ 1 (
        echo.
        echo Запускаю install_wsl.bat...
        call install_wsl.bat
    )
    echo.
    pause
    exit /b 1
)

echo [OK] WSL знайдено
echo.
echo [ІНФО] Конвертація шляху для WSL...
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
echo  КРОК 1: Перевірка buildozer у WSL
echo ============================================
echo.

wsl bash -c "cd \"%WSL_PATH%\" && if command -v buildozer >/dev/null 2>&1; then echo '[OK] Buildozer встановлено'; else echo '[!] Buildozer не знайдено, встановлюю...'; pip3 install --user buildozer >/dev/null 2>&1 && echo '[OK] Buildozer встановлено' || echo '[X] Помилка встановлення buildozer'; fi"

echo.
echo ============================================
echo  КРОК 2: Встановлення системних залежностей
echo ============================================
echo [ІНФО] Це може зайняти кілька хвилин...
echo.

wsl bash -c "sudo apt-get update -qq && sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev >/dev/null 2>&1 && echo '[OK] Системні залежності встановлено' || echo '[!] Деякі залежності можуть бути вже встановлені'"

echo.
echo ============================================
echo  КРОК 3: Збірка APK
echo ============================================
echo [ВАЖЛИВО] Перша збірка займе 20-30 хвилин!
echo          Buildozer завантажить Android SDK/NDK
echo.
echo Виконую buildozer android debug...
echo.

wsl bash -c "cd \"%WSL_PATH%\" && export PATH=\$PATH:~/.local/bin && buildozer android debug"

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo  [✓] УСПІХ! APK зібрано
    echo ============================================
    echo.
    echo APK файл знаходиться тут:
    
    REM Знаходимо APK файли
    if exist "bin\*.apk" (
        for %%f in (bin\*.apk) do (
            echo     %%f
            dir "%%f" | findstr /C:"%%f"
        )
    ) else (
        echo     bin\telegramuserbot-*.apk
        echo.
        echo [!] Файл не знайдено локально, перевірте папку bin\ у WSL
        wsl bash -c "cd \"%WSL_PATH%\" && ls -lh bin/*.apk 2>/dev/null || echo 'APK файл не знайдено'"
    )
    
    echo.
    echo Для встановлення на телефон:
    echo   1. Скопіюйте APK на телефон
    echo   2. Увімкніть "Дозволити встановлення з невідомих джерел"
    echo   3. Відкрийте APK файл на телефоні
    echo.
) else (
    echo.
    echo ============================================
    echo  [X] ПОМИЛКА при збірці APK
    echo ============================================
    echo.
    echo Можливі причини:
    echo   - Android SDK/NDK не завантажилися
    echo   - Проблеми з залежностями
    echo   - Помилки в коді
    echo.
    echo Спробуйте:
    echo   1. Перевірити лог вище на помилки
    echo   2. Очистити попередні збірки:
    echo      wsl bash -c "cd \"%WSL_PATH%\" && buildozer android clean"
    echo   3. Спробувати знову
    echo.
)

pause


