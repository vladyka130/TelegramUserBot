#!/bin/bash
# Виправлення Buildozer для Python 3.13 через встановлення setuptools

echo "============================================"
echo "Виправлення Buildozer для Python 3.13"
echo "============================================"
echo ""

# Шлях до pipx venv buildozer
PIPX_VENV="$HOME/.local/share/pipx/venvs/buildozer"

if [ ! -d "$PIPX_VENV" ]; then
    echo "[X] Помилка: pipx venv для buildozer не знайдено"
    echo "    Спочатку встановіть buildozer: pipx install buildozer"
    exit 1
fi

echo "[ІНФО] Знайдено pipx venv: $PIPX_VENV"
echo ""

# Активація venv та встановлення setuptools
echo "[ІНФО] Встановлення setuptools (містить distutils)..."
source "$PIPX_VENV/bin/activate"

# Встановлення setuptools
pip install setuptools

# Перевірка
echo ""
echo "============================================"
echo "Перевірка"
echo "============================================"
echo ""

python -c "from distutils.version import LooseVersion; print('[OK] distutils доступний')" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "[✓] Готово! Buildozer має працювати"
    echo "============================================"
    echo ""
    echo "Тепер спробуйте:"
    echo "  cd \"/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy\""
    echo "  buildozer android debug"
else
    echo ""
    echo "[!] distutils все ще не доступний"
    echo "    Спробуємо альтернативний спосіб..."
    exit 1
fi

deactivate

