# 🛠️ Збірка APK локально (PyCharm/VS Code)

## Варіант 1: PyCharm (найпростіший)

### Встановлення:
1. Встановіть **PyCharm Professional** (або Community + плагін)
2. Встановіть плагін **Buildozer** через Settings → Plugins
3. Налаштуйте Android SDK в Settings → Buildozer

### Використання:
1. Відкрийте проект в PyCharm
2. Перейдіть в папку `telegram_user_bot_kivy`
3. Створіть конфігурацію Buildozer
4. Натисніть "Build APK"

---

## Варіант 2: VS Code + Термінал

### Встановлення:
1. Встановіть **VS Code**
2. Встановіть розширення **Python**
3. Відкрийте термінал в VS Code

### Команди:
```bash
cd telegram_user_bot_kivy
pip install buildozer
buildozer android debug
```

---

## Варіант 3: Windows через WSL (рекомендовано для Windows)

### Кроки:
1. Встановіть WSL2 Ubuntu
2. Встановіть залежності:
```bash
sudo apt update
sudo apt install -y git zip unzip python3-pip openjdk-17-jdk
sudo apt install -y autoconf libtool pkg-config
sudo apt install -y zlib1g-dev libncurses5-dev libncursesw5-dev
sudo apt install -y cmake libffi-dev libssl-dev build-essential
```

3. Встановіть Buildozer:
```bash
pip3 install buildozer Cython
```

4. Скопіюйте проект в WSL:
```bash
cp -r /mnt/d/Python\ MY\ EXE/TelegramUserBot/telegram_user_bot_kivy ~/telegram_user_bot_kivy
cd ~/telegram_user_bot_kivy
```

5. Зберіть APK:
```bash
buildozer android debug
```

---

## Варіант 4: BeeWare Briefcase (альтернатива)

```bash
pip install briefcase
briefcase create android
briefcase build android
briefcase package android
```

---

## Варіант 5: GitHub Actions (вже налаштовано! ✅)

1. Зробіть `git push`
2. Перейдіть в **Actions** на GitHub
3. Завантажте готовий APK

**Це найпростіший спосіб - нічого встановлювати не потрібно!**

---

## Який варіант обрати?

- **GitHub Actions** - якщо хочете автоматизацію (вже налаштовано)
- **PyCharm** - якщо хочете GUI та зручний інтерфейс
- **VS Code + термінал** - якщо зручно працювати з терміналом
- **WSL** - якщо на Windows і потрібна локальна збірка

**Рекомендація:** Використовуйте GitHub Actions - воно вже працює! 🚀

