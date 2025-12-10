#!/bin/bash
# Скрипт для збірки APK через WSL (Linux)

echo "============================================"
echo "Збірка APK для Telegram User Bot"
echo "============================================"
echo ""

# Перевірка чи ми в правильній папці
if [ ! -f "buildozer.spec" ]; then
    echo "[ПОМИЛКА] buildozer.spec не знайдено!"
    echo "Запустіть скрипт з папки telegram_user_bot_kivy"
    exit 1
fi

# Встановлення buildozer (якщо потрібно)
if ! command -v buildozer &> /dev/null; then
    echo "[1/4] Встановлення buildozer..."
    pip3 install --user buildozer
    export PATH=$PATH:~/.local/bin
else
    echo "[OK] Buildozer вже встановлений"
fi

# Встановлення системних залежностей (якщо потрібно)
echo ""
echo "[2/4] Перевірка системних залежностей..."
sudo apt-get update -qq
sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev > /dev/null 2>&1

# Очищення попередніх збірок (опціонально)
read -p "Очистити попередні збірки? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "[3/4] Очищення попередніх збірок..."
    buildozer android clean
fi

# Збірка APK
echo ""
echo "[4/4] Збірка APK (це займе 20-30 хвилин при першій збірці)..."
echo ""
buildozer android debug

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "[УСПІХ] APK зібрано!"
    echo "============================================"
    echo ""
    echo "APK файл знаходиться тут:"
    ls -lh bin/*.apk 2>/dev/null || echo "bin/telegramuserbot-*.apk"
    echo ""
else
    echo ""
    echo "============================================"
    echo "[ПОМИЛКА] Не вдалося зібрати APK"
    echo "============================================"
    echo ""
fi




