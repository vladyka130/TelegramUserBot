# Детальна інструкція зі збірки APK

## Варіант 1: Linux (найпростіше)

### Крок 1: Встановлення залежностей

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Встановлення Buildozer
pip3 install --user buildozer
export PATH=$PATH:~/.local/bin
```

### Крок 2: Клонування/копіювання проекту

```bash
cd telegram_user_bot_kivy
```

### Крок 3: Перша збірка (завантажить Android SDK/NDK)

```bash
buildozer android debug
```

Це займе 20-30 хвилин при першій збірці (завантаження SDK, NDK, компіляція).

### Крок 4: Знайти APK

```bash
ls -lh bin/*.apk
```

APK буде в папці `bin/`

---

## Варіант 2: Windows через WSL2

### Крок 1: Встановлення WSL2

```powershell
# В PowerShell (адміністратор)
wsl --install
```

Перезавантажте комп'ютер.

### Крок 2: Запуск WSL

```bash
# Відкрити WSL (Ubuntu)
wsl
```

### Крок 3: Встановлення залежностей в WSL

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

pip3 install --user buildozer
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc
```

### Крок 4: Доступ до файлів Windows

```bash
# Проект на диску D: буде доступний як /mnt/d/
cd /mnt/d/ПУТЬ/ДО/telegram_user_bot_kivy

# Або скопіюйте проект в WSL
cp -r /mnt/d/Python\ MY\ EXE/TelegramUserBot/telegram_user_bot_kivy ~/
cd ~/telegram_user_bot_kivy
```

### Крок 5: Збірка

```bash
buildozer android debug
```

---

## Варіант 3: Використання готового Docker

```bash
# Клонувати python-for-android docker
git clone https://github.com/kivy/python-for-android
cd python-for-android

# Запустити Docker контейнер
docker run --rm -v $(pwd):/app kivy/buildozer buildozer android debug
```

---

## Налаштування buildozer.spec

Основні параметри:

```ini
# Назва додатка
title = Telegram User Bot

# Ім'я пакета
package.name = telegramuserbot

# Версія
version = 1.0

# Мінімальна Android версія
android.minapi = 21

# Цільова Android версія
android.api = 33

# Архітектури (для меншого розміру можна вибрати одну)
android.archs = arm64-v8a, armeabi-v7a

# Дозволи
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,WAKE_LOCK
```

---

## Оптимізація розміру APK

### Варіант 1: Тільки одна архітектура

В `buildozer.spec`:
```ini
android.archs = arm64-v8a  # Тільки 64-bit ARM (більшість сучасних телефонів)
```

### Варіант 2: Split APK (різні APK для кожної архітектури)

```bash
buildozer android release
```

---

## Збірка release версії (підписана)

### 1. Створити ключ

```bash
keytool -genkey -v -keystore telegram-user-bot.keystore -alias telegramuserbot -keyalg RSA -keysize 2048 -validity 10000
```

### 2. Налаштувати buildozer.spec

```ini
# (str) Full path to the keystore
android.keystore = telegram-user-bot.keystore

# (str) Keystore password
android.keystore_password = ваш_пароль

# (str) Key alias
android.keyalias = telegramuserbot

# (str) Key password
android.keypassword = ваш_пароль
```

### 3. Зібрати release

```bash
buildozer android release
```

---

## Усунення проблем

### Помилка "SDK not found"

```bash
# Перевірте налаштування
buildozer android debug 2>&1 | grep -i sdk

# Або встановіть SDK вручну через Android Studio
```

### Помилка з Telethon/SSL

Додайте в `buildozer.spec`:
```ini
requirements = python3,kivy,telethon,certifi,pyopenssl,cryptography
```

### Повільна збірка

```bash
# Використайте кеш
buildozer android debug --verbose
```

### Очищення для чистої збірки

```bash
buildozer android clean
rm -rf .buildozer
buildozer android debug
```

---

## Альтернатива: GitHub Actions (CI/CD)

Можна налаштувати автоматичну збірку через GitHub Actions - APK буде збиратися автоматично при кожному коміті.

---

## Тестування APK

### Встановлення через ADB

```bash
adb install bin/telegramuserbot-*.apk
```

### Перевірка логів

```bash
adb logcat | grep python
```

---

## Підсумок

**Найпростіший шлях:**
1. Встановити WSL2 на Windows
2. Встановити buildozer в WSL
3. Запустити `buildozer android debug`
4. Чекати 20-30 хвилин
5. Отримати APK в `bin/`

**Альтернатива:** Використати Linux віртуальну машину або CI/CD.




