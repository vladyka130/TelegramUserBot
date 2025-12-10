# 🔧 Виправлення для Kali Linux з Python 3.13

## Проблема
Kali Linux використовує Python 3.13, а Buildozer не працює з Python 3.12+.

## Рішення 1: pipx (рекомендовано для додатків)

```bash
# Встановити pipx
sudo apt install pipx
pipx ensurepath

# Встановити Buildozer через pipx
pipx install buildozer

# Перевірити
buildozer --version
```

## Рішення 2: Встановити Python 3.11 окремо

```bash
# Додати deadsnakes PPA (для Ubuntu/Debian) або встановити зі звичайних репозиторіїв
sudo apt update

# Спробувати встановити Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-pip python3.11-dev

# Якщо python3.11 недоступний, спробувати python3.10
sudo apt install python3.10 python3.10-venv python3.10-pip python3.10-dev

# Створити venv з Python 3.11 (або 3.10)
python3.11 -m venv buildozer_venv
# або
python3.10 -m venv buildozer_venv

# Активувати
source buildozer_venv/bin/activate

# Встановити Buildozer
pip install buildozer

# Перевірити
python --version  # Має бути 3.11.x або 3.10.x
buildozer --version
```

## Рішення 3: Використати Docker (якщо інші не спрацюють)

```bash
# Завантажити Docker образ з Python 3.11
docker pull kivy/buildozer:latest

# Або створити свій Dockerfile з Python 3.11
```

## Рішення 4: Через --break-system-packages (не рекомендовано)

⚠️ **УВАГА:** Це може зламати системні пакети Python!

```bash
pip3 install --user --break-system-packages buildozer
export PATH=$PATH:~/.local/bin
```

---

## Рекомендований підхід для Kali

**Крок 1:** Встановити pipx
```bash
sudo apt install pipx
pipx ensurepath
# Закрити і відкрити термінал знову
```

**Крок 2:** Встановити Buildozer
```bash
pipx install buildozer
```

**Крок 3:** Перевірити
```bash
buildozer --version
```

**Крок 4:** Зібрати APK
```bash
cd "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy"
buildozer android debug
```

---

## Якщо Python 3.11/3.10 недоступний в репозиторіях

Можна скомпілювати Python 3.11 з вихідних кодів або використати pyenv:

```bash
# Встановити pyenv
curl https://pyenv.run | bash

# Додати до .bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Встановити Python 3.11
pyenv install 3.11.9

# Використати Python 3.11 для проекту
cd "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy"
pyenv local 3.11.9
python -m venv buildozer_venv
source buildozer_venv/bin/activate
pip install buildozer
```

