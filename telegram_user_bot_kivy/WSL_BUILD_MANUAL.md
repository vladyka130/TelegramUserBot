# 📱 Збірка APK вручну через WSL

## Крок 1: Перехід до папки проекту

```bash
# Ваш проект на диску D:, тому в WSL це:
cd "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy"

# Або скопіюйте проект в WSL (швидше):
cp -r "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy" ~/
cd ~/telegram_user_bot_kivy
```

## Крок 2: Оновлення системи

```bash
sudo apt update
sudo apt upgrade -y
```

## Крок 3: Встановлення системних залежностей

```bash
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
  autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
  libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

## Крок 4: Встановлення Buildozer

```bash
pip3 install --user buildozer
export PATH=$PATH:~/.local/bin

# Додати до .bashrc (щоб не вводити щоразу)
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
```

## Крок 5: Перевірка встановлення

```bash
buildozer --version
```

Має показати версію Buildozer.

## Крок 6: Збірка APK

```bash
# Переконайтеся, що ви в папці з buildozer.spec
cd ~/telegram_user_bot_kivy  # або ваш шлях

# Очистити попередні збірки (якщо були проблеми)
# buildozer android clean

# Почати збірку
buildozer android debug
```

**Перша збірка займе 20-30 хвилин** - Buildozer завантажить Android SDK та NDK.

## Крок 7: Знайти готовий APK

```bash
ls -lh bin/*.apk
```

APK буде в папці `bin/telegramuserbot-*.apk`

---

## Швидка команда (все разом)

Якщо хочете виконати все одразу:

```bash
# Перехід до проекту
cd "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy" || \
  (cp -r "/mnt/d/Python MY EXE/TelegramUserBot/telegram_user_bot_kivy" ~/ && \
   cd ~/telegram_user_bot_kivy)

# Оновлення та встановлення
sudo apt update && \
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip \
  autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
  libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev && \
pip3 install --user buildozer && \
export PATH=$PATH:~/.local/bin && \
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc

# Перевірка
buildozer --version

# Збірка
buildozer android debug
```

---

## Якщо щось пішло не так

### Помилка "command not found: buildozer"
```bash
export PATH=$PATH:~/.local/bin
source ~/.bashrc
```

### Помилка з правами доступу
```bash
# Перевірте чи ви в правильній папці
pwd
ls buildozer.spec
```

### Очищення для чистої збірки
```bash
buildozer android clean
rm -rf .buildozer
buildozer android debug
```

---

## Альтернатива: Використати скрипт з Windows

Просто запустіть з Windows:
- `setup_wsl_environment.bat` - для налаштування
- `build_apk_simple.bat` - для збірки

Це простіше і автоматичніше! 😉



