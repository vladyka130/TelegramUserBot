# Швидкий старт - Kivy версія

## Встановлення залежностей

### Варіант 1: Автоматично (Windows)

Подвійний клік на файл:
```
install_dependencies.bat
```

### Варіант 2: Вручну

Відкрийте термінал в папці `telegram_user_bot_kivy` і виконайте:

```bash
pip install kivy>=2.1.0
pip install telethon>=1.28.0
pip install certifi
```

### Варіант 3: Через requirements.txt

```bash
pip install -r requirements.txt
```

## Запуск на Windows (для тестування)

```bash
python main.py
```

**Примітка:** На Windows Kivy відкриє вікно для тестування. Для Android потрібна збірка через Buildozer.

## Запуск на Android

1. Встановіть Buildozer (див. BUILD_INSTRUCTIONS.md)
2. Виконайте: `buildozer android debug`
3. Встановіть APK на телефон

## Можливі проблеми

### "ModuleNotFoundError: No module named 'kivy'"

Встановіть залежності:
```bash
pip install kivy
```

### "No module named 'telethon'"

```bash
pip install telethon
```

### Використання віртуального середовища

Якщо у вас є venv (наприклад Grafik_venv):
```bash
# Активація venv
Grafik_venv\Scripts\activate

# Встановлення залежностей
pip install kivy telethon certifi

# Запуск
python telegram_user_bot_kivy\main.py
```




