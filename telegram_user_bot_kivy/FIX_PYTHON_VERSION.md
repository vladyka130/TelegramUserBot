# 🔧 Виправлення помилки з Python 3.13

## Проблема

Buildozer не працює з Python 3.12+ через відсутність модуля `distutils`.

## Рішення: Використати системний Python

### Крок 1: Деактивувати venv

```bash
# Вийти з віртуального середовища
deactivate
```

### Крок 2: Перевірити системний Python

```bash
# Перевірка версії системного Python
python3 --version

# Має бути Python 3.10 або 3.11 (не 3.12+)
```

### Крок 3: Встановити Buildozer глобально (або в користувацький каталог)

```bash
# Встановлення Buildozer для користувача (не в venv)
pip3 install --user buildozer

# Додати до PATH
export PATH=$PATH:~/.local/bin
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
```

### Крок 4: Перевірити

```bash
# Має показати версію Buildozer
buildozer --version

# Має бути системний Python
which python3
python3 --version
```

### Крок 5: Перейти до проекту та зібрати

```bash
cd "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy"
# або
cd ~/telegram_user_bot_kivy

buildozer android debug
```

---

## Альтернатива: Встановити Python 3.11 окремо

Якщо системний Python теж 3.12+, можна встановити Python 3.11:

```bash
# Встановити Python 3.11
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-pip

# Створити venv з Python 3.11
python3.11 -m venv buildozer_venv
source buildozer_venv/bin/activate

# Встановити Buildozer
pip install buildozer

# Перевірити
python --version  # Має бути 3.11.x
buildozer --version
```

---

## Швидке рішення (рекомендовано)

Просто **вийдіть з venv** і використайте системний Python:

```bash
deactivate
pip3 install --user buildozer
export PATH=$PATH:~/.local/bin
cd "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy"
buildozer android debug
```

