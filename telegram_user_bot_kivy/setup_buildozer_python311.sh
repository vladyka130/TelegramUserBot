#!/bin/bash
# Скрипт для встановлення Python 3.11 та Buildozer

echo "============================================"
echo "Встановлення Python 3.11 та Buildozer"
echo "============================================"
echo ""

# Перевірка чи встановлений Python 3.11
if command -v python3.11 &> /dev/null; then
    echo "[OK] Python 3.11 вже встановлений"
    python3.11 --version
else
    echo "[ІНФО] Встановлення Python 3.11..."
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-pip python3.11-dev
    
    if ! command -v python3.11 &> /dev/null; then
        echo "[!] Python 3.11 не встановлено автоматично"
        echo "    Спробуємо встановити Python 3.10..."
        sudo apt install -y python3.10 python3.10-venv python3.10-pip python3.10-dev
        
        if ! command -v python3.10 &> /dev/null; then
            echo "[X] Помилка: Python 3.10/3.11 не доступний в репозиторіях"
            echo ""
            echo "Альтернативи:"
            echo "1. Встановити через deadsnakes PPA (Ubuntu/Debian)"
            echo "2. Скомпілювати Python 3.11 з вихідних кодів"
            echo "3. Використати pyenv"
            exit 1
        else
            PYTHON_VERSION="3.10"
            PYTHON_CMD="python3.10"
        fi
    else
        PYTHON_VERSION="3.11"
        PYTHON_CMD="python3.11"
    fi
fi

echo ""
echo "[ІНФО] Використовую Python $PYTHON_VERSION"
echo ""

# Створення venv з Python 3.11/3.10
echo "============================================"
echo "Створення віртуального середовища"
echo "============================================"
echo ""

VENV_DIR="$HOME/buildozer_venv"

if [ -d "$VENV_DIR" ]; then
    echo "[ІНФО] Віртуальне середовище вже існує"
    read -p "Перестворити? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
else
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

echo "[OK] Віртуальне середовище створено: $VENV_DIR"
echo ""

# Активація та встановлення Buildozer
echo "============================================"
echo "Встановлення Buildozer"
echo "============================================"
echo ""

source "$VENV_DIR/bin/activate"

# Перевірка версії Python в venv
echo "Версія Python в venv:"
python --version

# Оновлення pip
pip install --upgrade pip

# Встановлення Buildozer
pip install buildozer

# Перевірка
echo ""
echo "============================================"
echo "Перевірка встановлення"
echo "============================================"
echo ""

buildozer --version

echo ""
echo "============================================"
echo "[✓] Готово!"
echo "============================================"
echo ""
echo "Для використання Buildozer:"
echo ""
echo "1. Активуйте середовище:"
echo "   source $VENV_DIR/bin/activate"
echo ""
echo "2. Перейдіть до проекту:"
echo "   cd \"/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy\""
echo ""
echo "3. Запустіть збірку:"
echo "   buildozer android debug"
echo ""

