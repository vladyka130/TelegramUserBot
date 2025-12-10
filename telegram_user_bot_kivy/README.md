# Telegram User Bot - Kivy версія для Android

**Набагато простіше ніж Flutter!** Тут залишається весь Python код, змінюється тільки GUI.

## Переваги Kivy версії:

✅ **Не потрібен Flutter SDK** - тільки Python + Kivy  
✅ **Вся логіка залишається Python** - Telethon працює як є  
✅ **Швидше зібрати APK** - через Buildozer  
✅ **Менше нових інструментів** - все знайоме  

## Швидкий старт

### 1. Встановлення Buildozer

```bash
# Windows (через WSL або Linux)
pip install buildozer

# Linux
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
pip3 install buildozer
```

### 2. Збірка APK

```bash
cd telegram_user_bot_kivy
buildozer android debug
```

APK буде в `bin/telegramuserbot-*.apk`

## Структура

- `main.py` - Головний файл з Kivy GUI та всією логікою
- `requirements.txt` - Python залежності
- `buildozer.spec` - Конфігурація для збірки APK
- `emojis/` - Папка для стікерів (створюється автоматично)

## Відмінності від оригіналу

**Що залишилося без змін:**
- Вся логіка Telethon
- Парсери розкладу
- Розсилка повідомлень
- Обробка стікерів
- Конфігурація

**Що змінилося:**
- GUI: CustomTkinter → Kivy
- Діалоги: tkinter → Kivy Popup
- Async: залишилося таким же (threading + asyncio)

## Налаштування

### Android дозволи

Вже налаштовані в `buildozer.spec`:
- INTERNET
- READ_EXTERNAL_STORAGE
- WRITE_EXTERNAL_STORAGE
- WAKE_LOCK

### Зміна версії

Відредагуйте `buildozer.spec`:
```ini
version = 1.0  # Змініть на потрібну версію
```

## Збірка на Linux (рекомендовано)

Buildozer найкраще працює на Linux. Якщо у вас Windows:

1. **WSL2** (рекомендовано):
   ```bash
   wsl --install
   # Потім встановіть buildozer в WSL
   ```

2. **Linux віртуальна машина** (VirtualBox, VMware)

3. **GitHub Actions** (CI/CD для автоматичної збірки)

## Можливі проблеми

### "buildozer: command not found"
```bash
pip install buildozer
# Або
pip3 install buildozer
```

### Помилки збірки
```bash
# Очистити кеш
buildozer android clean

# Перезібрати
buildozer android debug
```

### SSL помилки
Додайте в `buildozer.spec`:
```ini
requirements = python3,kivy,telethon,certifi,pyopenssl,cryptography
```

## Тестування

Після збірки:
1. Встановіть APK на Android пристрій
2. Дозвольте "Джерела невідомого походження"
3. Запустіть додаток
4. Введіть API ID/HASH
5. Завантажте чати
6. Налаштуйте розсилку

## Детальна інструкція

Див. `BUILD_INSTRUCTIONS.md` для повного гайду.




