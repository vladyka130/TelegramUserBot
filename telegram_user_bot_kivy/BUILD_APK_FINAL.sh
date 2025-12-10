#!/bin/bash
# 100% робочий скрипт для збірки APK на Kali Linux

set -e  # Зупинитися при помилці

echo "============================================"
echo "ЗБІРКА APK - ПОКРОКОВІ КОМАНДИ"
echo "============================================"
echo ""

# КРОК 1: Встановити setuptools в pipx venv
echo "[1/5] Виправлення Buildozer для Python 3.13..."
source ~/.local/share/pipx/venvs/buildozer/bin/activate
pip install --upgrade setuptools
python -c "from distutils.version import LooseVersion; print('OK')" || {
    echo "[!] distutils не працює, встановлюємо Python 3.11 через pyenv..."
    deactivate
    
    # Встановити pyenv
    if ! command -v pyenv &> /dev/null; then
        curl https://pyenv.run | bash
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
    fi
    
    # Встановити Python 3.11
    pyenv install 3.11.9 2>/dev/null || pyenv install 3.11.0
    
    # Створити venv з Python 3.11
    ~/.pyenv/versions/3.11.9/bin/python -m venv ~/buildozer_venv || \
    ~/.pyenv/versions/3.11.0/bin/python -m venv ~/buildozer_venv
    
    source ~/buildozer_venv/bin/activate
    pip install --upgrade pip
    pip install buildozer
}
deactivate 2>/dev/null || true

# КРОК 2: Встановити системні залежності
echo ""
echo "[2/5] Встановлення системних залежностей..."
sudo apt update -qq
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev 2>&1 | grep -v "^$" || true

# КРОК 3: Активувати правильне середовище
echo ""
echo "[3/5] Активування середовища..."
if [ -d ~/buildozer_venv ]; then
    source ~/buildozer_venv/bin/activate
    echo "[OK] Використовую venv з Python 3.11"
else
    source ~/.local/share/pipx/venvs/buildozer/bin/activate
    echo "[OK] Використовую pipx venv"
fi

# Перевірка
python --version
buildozer --version

# КРОК 4: Перейти до проекту
echo ""
echo "[4/5] Перехід до проекту..."
cd "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy"
pwd

# Перевірка buildozer.spec
if [ ! -f "buildozer.spec" ]; then
    echo "[X] ПОМИЛКА: buildozer.spec не знайдено!"
    exit 1
fi

# КРОК 5: Збірка APK
echo ""
echo "[5/5] ЗБІРКА APK (це займе 20-30 хвилин)..."
echo "============================================"
echo ""

buildozer android debug

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "[✓] УСПІХ! APK зібрано!"
    echo "============================================"
    echo ""
    echo "APK файл:"
    ls -lh bin/*.apk 2>/dev/null || echo "Перевірте папку bin/"
else
    echo ""
    echo "[X] Помилка збірки. Перевірте логи вище."
    exit 1
fi

