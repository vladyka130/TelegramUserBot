# Як встановити та запустити Kivy версію

## Проблема: "ModuleNotFoundError: No module named 'kivy'"

Це означає, що Kivy не встановлений у вашому Python середовищі.

## Рішення 1: Автоматично (рекомендовано)

**Подвійний клік на файл:**
```
setup_venv.bat
```

Цей скрипт:
1. Знайде ваше віртуальне середовище (Grafik_venv)
2. Встановить Kivy, Telethon, certifi
3. Готово до запуску!

## Рішення 2: Вручну через venv

```bash
# 1. Активуйте venv
cd ..
Grafik_venv\Scripts\activate

# 2. Встановіть залежності
cd telegram_user_bot_kivy
pip install kivy telethon certifi

# 3. Запустіть
python main.py
```

## Рішення 3: Без venv (глобальне встановлення)

```bash
pip install kivy telethon certifi
python main.py
```

## Перевірка встановлення

```bash
python -c "import kivy; print('Kivy OK:', kivy.__version__)"
python -c "import telethon; print('Telethon OK')"
```

Якщо обидва працюють - все готово!

## Запуск

**Варіант 1:** Подвійний клік на `run.bat`

**Варіант 2:** В терміналі:
```bash
python main.py
```

## Важливо!

- На Windows Kivy відкриє вікно для тестування GUI
- Для Android потрібна збірка через Buildozer (див. BUILD_INSTRUCTIONS.md)
- Переконайтеся, що використовуєте правильне Python середовище




