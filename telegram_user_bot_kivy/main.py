"""
Telegram User Bot - Kivy версія для Android
Портування з CustomTkinter на Kivy
"""
import sys
import os
import re
import json
import asyncio
import threading
from datetime import datetime, timedelta

# Для Android - використовуємо Kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp

# Telethon імпорти (працюють на Android)
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError,
    PhoneCodeExpiredError, PhoneNumberInvalidError
)

# --- Константи ---
CONFIG_FILE = "config.json"
EMOJI_DIR = "emojis"

# Шлях для сесії (Android: використовуємо app storage)
if platform == 'android':
    from android.storage import app_storage_path
    APPDIR = app_storage_path()
    os.makedirs(APPDIR, exist_ok=True)
    SESSION_PATH = os.path.join(APPDIR, "my_account")
else:
    APPDIR = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "TelegramUserSender")
    os.makedirs(APPDIR, exist_ok=True)
    SESSION_PATH = os.path.join(APPDIR, "my_account")

if not os.path.exists(EMOJI_DIR):
    os.makedirs(EMOJI_DIR)

# --- Всі функції з оригінального коду (залишаються без змін) ---
# (імпортують з окремого модуля для чистоти, але можна і тут залишити)
exec(open('telegram_logic.py').read()) if os.path.exists('telegram_logic.py') else None

# Якщо модуль не існує - копіюємо логіку сюди
# Для простоти - весь код буде в одному файлі для Android


# ============= ВСЯ ЛОГІКА З ОРИГІНАЛЬНОГО ФАЙЛУ (КОПІЮЄТЬСЯ) =============
async def _send_one_message(client, chat, msg_text, log_callback):
    """Відправка одного повідомлення з підтримкою стікерів"""
    try:
        parts = re.split(r"(\[\[emoji:.*?\]\])", msg_text)
        files_to_send = []
        text_parts = []

        for part in parts:
            if not part:
                continue
            if part.startswith("[[emoji:") and part.endswith("]]"):
                fname = part.replace("[[emoji:", "").replace("]]", "")
                filepath = os.path.join(EMOJI_DIR, fname)
                if os.path.exists(filepath):
                    files_to_send.append(filepath)
                else:
                    log_callback(f"❌ Файл {fname} не знайдено в {EMOJI_DIR}")
            else:
                text_parts.append(part.strip())

        final_text = " ".join(p for p in text_parts if p)

        if files_to_send:
            if final_text:
                await client.send_message(chat, final_text)
                log_callback(f"✅ Текст: {final_text}")
            for f in files_to_send:
                try:
                    await client.send_file(chat, file=f)
                    log_callback(f"✅ Стікер {os.path.basename(f)} відправлено")
                except Exception as e:
                    log_callback(f"❌ Помилка при відправці стікера {f}: {e}")
        elif final_text:
            await client.send_message(chat, final_text)
            log_callback(f"✅ Повідомлення надіслано: {final_text}")

    except Exception as e:
        log_callback(f"❌ Помилка відправки: {e}")


def _parse_schedule_tokens(text: str):
    """Парсинг розкладу - копія з оригіналу"""
    daily_times = []
    absolute_times = []

    if not text.strip():
        return daily_times, absolute_times

    now = datetime.now()
    for raw in text.split(","):
        token = raw.strip()
        if not token:
            continue

        low = token.lower()
        m = re.match(r"^(сьогодні|завтра|післязавтра)\s+(\d{1,2}):(\d{2})$", low)
        if m:
            kw, hh, mm = m.groups()
            hh, mm = int(hh), int(mm)
            base = now.replace(second=0, microsecond=0)
            if kw == "сьогодні":
                dt = base.replace(hour=hh, minute=mm)
            elif kw == "завтра":
                dt = (base + timedelta(days=1)).replace(hour=hh, minute=mm)
            else:
                dt = (base + timedelta(days=2)).replace(hour=hh, minute=mm)
            absolute_times.append(dt)
            continue

        m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$", token)
        if m:
            y, mo, d, h, mi = map(int, m.groups())
            absolute_times.append(datetime(y, mo, d, h, mi, 0, 0))
            continue

        m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})$", token)
        if m:
            d, mo, y, h, mi = map(int, m.groups())
            absolute_times.append(datetime(y, mo, d, h, mi, 0, 0))
            continue

        m = re.match(r"^(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{2})$", token)
        if m:
            d, mo, h, mi = map(int, m.groups())
            absolute_times.append(datetime(now.year, mo, d, h, mi, 0, 0))
            continue

        m = re.match(r"^(\d{1,2}):(\d{2})$", token)
        if m:
            hh, mm = map(int, m.groups())
            daily_times.append(f"{hh:02d}:{mm:02d}")
            continue

        raise ValueError(
            f"Невірний формат розкладу: «{token}». "
            f"Приклади: 09:00, 06.10 09:15, 07.10.2025 10:30, 2025-10-08 14:45, завтра 09:00."
        )

    daily_times = sorted(set(daily_times))
    absolute_times = sorted(set(absolute_times))
    return daily_times, absolute_times


async def send_periodic(client, chat, messages, interval, limit, log_callback, stop_check):
    """Періодична розсилка"""
    if not messages:
        log_callback("❌ Немає повідомлень для відправки.")
        return
    
    count = 0
    idx = 0
    n = len(messages)
    
    # Якщо limit = 0, відправляємо тільки один раз
    if limit == 0:
        msg = messages[idx % n]
        try:
            await _send_one_message(client, chat, msg, log_callback)
            log_callback("✅ Повідомлення відправлено один раз (limit=0).")
        except Exception as e:
            log_callback(f"❌ Помилка відправки: {e}")
        return
    
    # Якщо limit > 0, відправляємо limit повідомлень
    while True:
        if stop_check():
            log_callback("⏹️ Відправку зупинено користувачем.")
            break
        
        if count >= limit:
            log_callback(f"⏹️ Відправка завершена (надіслано {count} повідомлень).")
            break
        
        msg = messages[idx % n]
        idx += 1
        await _send_one_message(client, chat, msg, log_callback)
        count += 1
        
        # Якщо досягли ліміту - зупиняємося без затримки
        if count >= limit:
            log_callback(f"⏹️ Відправка завершена (надіслано {count} повідомлень).")
            break
        
        # Чекаємо інтервал перед наступним повідомленням
        await asyncio.sleep(interval)


async def send_by_schedule(client, chat, messages, daily_times, absolute_times, repeat_daily, log_callback, stop_check):
    """Розсилка за розкладом"""
    if not messages:
        log_callback("❌ Немає повідомлень для відправки.")
        return

    sent_today = set()
    sent_daily_once = set()
    fired_abs = set()

    idx = 0
    n = len(messages)

    def next_msg():
        nonlocal idx
        m = messages[idx % n]
        idx += 1
        return m

    while True:
        if stop_check():
            log_callback("⏹️ Розсилку за розкладом зупинено користувачем.")
            break

        now = datetime.now()
        current_min = now.strftime("%H:%M")
        current_abs_key = now.strftime("%Y-%m-%d %H:%M")

        if daily_times and current_min in daily_times:
            should_send = False
            if repeat_daily:
                should_send = current_min not in sent_today
            else:
                should_send = current_min not in sent_daily_once
            if should_send:
                try:
                    await _send_one_message(client, chat, next_msg(), log_callback)
                    if repeat_daily:
                        sent_today.add(current_min)
                    else:
                        sent_daily_once.add(current_min)
                except Exception as e:
                    log_callback(f"❌ Помилка при відправці о {current_min}: {e}")

        if absolute_times:
            to_fire = [dt for dt in absolute_times if dt.strftime("%Y-%m-%d %H:%M") == current_abs_key]
            for dt in to_fire:
                key = dt.strftime("%Y-%m-%d %H:%M")
                if key in fired_abs:
                    continue
                try:
                    await _send_one_message(client, chat, next_msg(), log_callback)
                    fired_abs.add(key)
                except Exception as e:
                    log_callback(f"❌ Помилка при відправці о {key}: {e}")

        if current_min == "00:00":
            sent_today.clear()

        await asyncio.sleep(30)


def save_config(data):
    """Збереження конфігурації"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_config():
    """Завантаження конфігурації"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def start_async_loop(loop):
    """Запуск async loop у окремому потоці"""
    asyncio.set_event_loop(loop)
    loop.run_forever()

# ============= КІНЕЦЬ ЛОГІКИ =============


# ============= KIVY GUI =============
class TelegramUserApp(App):
    """Головний додаток Kivy"""
    
    def build(self):
        return TelegramUserRoot()
    
    def on_stop(self):
        """При закритті додатка"""
        if hasattr(self.root, 'on_closing'):
            self.root.on_closing()


class TelegramUserRoot(BoxLayout):
    """Головний корінь GUI"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(5)
        self.spacing = dp(5)
        
        # Async loop для Telethon
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=start_async_loop, args=(self.loop,), daemon=True)
        self.loop_thread.start()
        
        self.client = None
        self.stop_flag = False
        self.chat_map = {}
        self.cfg = load_config()
        
        # Відстеження зміни орієнтації
        Window.bind(on_resize=self._on_resize)
        
        self.build_ui()
        
        # Автоматична перевірка авторизації при запуску
        Clock.schedule_once(lambda dt: self._auto_check_auth(), 0.5)
    
    def _on_resize(self, window, width, height):
        """Адаптація інтерфейсу при зміні орієнтації"""
        # Адаптуємо висоту логів в залежності від орієнтації
        if hasattr(self, 'log_label') and self.log_label.parent:
            for child in self.children:
                if isinstance(child, ScrollView):
                    for inner_child in child.children:
                        if isinstance(inner_child, BoxLayout):
                            for log_item in inner_child.children:
                                if isinstance(log_item, ScrollView) and log_item.children[0] == self.log_label:
                                    new_height = dp(100) if self._is_landscape() else dp(150)
                                    log_item.height = new_height
                                    break
    
    def _is_landscape(self):
        """Перевірка чи екран в горизонтальному положенні"""
        return Window.width > Window.height
    
    def _auto_check_auth(self):
        """Автоматична перевірка авторизації при запуску"""
        # Перевіряємо чи є збережені API credentials
        api_id = self.cfg.get('api_id')
        api_hash = self.cfg.get('api_hash')
        
        if not api_id or not api_hash:
            self.log("ℹ️ Введіть API ID та HASH для авторизації")
            return
        
        # Якщо credentials є - намагаємося підключитися
        self.log("🔄 Перевірка збереженої авторизації...")
        
        async def check_auth():
            try:
                # Перевіряємо чи існує файл сесії
                session_file = f"{SESSION_PATH}.session"
                if not os.path.exists(session_file):
                    self.log("ℹ️ Сесія не знайдена. Потрібна перша авторизація.")
                    return
                
                # Ініціалізуємо клієнт зі збереженими credentials
                if self.client is None:
                    self.client = TelegramClient(SESSION_PATH, api_id, api_hash)
                
                await self.client.connect()
                
                # Перевіряємо чи вже авторизовано
                if await self.client.is_user_authorized():
                    self.log("✅ Авторизація знайдена! Завантажую чати...")
                    
                    # Автоматично завантажуємо чати
                    try:
                        dialogs = await self.client.get_dialogs()
                        self.chat_map = {d.name: d.id for d in dialogs}
                        chats_list = list(self.chat_map.keys()) or ["(нема чатів)"]
                        
                        Clock.schedule_once(lambda dt: self._update_chats_list(chats_list), 0)
                        
                        # Отримуємо інформацію про користувача
                        me = await self.client.get_me()
                        uname = f"@{me.username}" if getattr(me, "username", None) else ""
                        self.log(f"✅ Авторизовано як: {me.first_name} {uname}")
                        self.log(f"✅ Готово до роботи! Виберіть чат та запустіть розсилку.")
                    except Exception as e:
                        self.log(f"⚠️ Помилка завантаження чатів: {e}")
                else:
                    self.log("ℹ️ Авторизація не знайдена. Введіть код при першій розсилці.")
                    
            except Exception as e:
                self.log(f"⚠️ Помилка перевірки авторизації: {e}")
        
        asyncio.run_coroutine_threadsafe(check_auth(), self.loop)
    
    def build_ui(self):
        """Побудова інтерфейсу для смартфона"""
        # ScrollView для всього контенту (важливо для маленьких екранів)
        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True)
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(5), spacing=dp(5))
        content.bind(minimum_height=content.setter('height'))
        
        # Компактні розміри для смартфона
        FIELD_HEIGHT = dp(35)
        LABEL_HEIGHT = dp(25)
        BTN_HEIGHT = dp(45)
        SMALL_SPACING = dp(3)
        
        # API ID - компактний рядок
        api_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=FIELD_HEIGHT, spacing=SMALL_SPACING)
        api_row.add_widget(Label(text='API ID:', size_hint_x=0.25, text_size=(None, None), halign='left'))
        self.api_id_input = TextInput(text=str(self.cfg.get('api_id', '')), multiline=False, size_hint_x=0.75, font_size=dp(14))
        api_row.add_widget(self.api_id_input)
        content.add_widget(api_row)
        
        # API HASH - компактний рядок
        hash_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=FIELD_HEIGHT, spacing=SMALL_SPACING)
        hash_row.add_widget(Label(text='API HASH:', size_hint_x=0.25, text_size=(None, None), halign='left'))
        self.api_hash_input = TextInput(text=self.cfg.get('api_hash', ''), password=True, multiline=False, size_hint_x=0.75, font_size=dp(14))
        hash_row.add_widget(self.api_hash_input)
        content.add_widget(hash_row)
        
        # Чати - компактний рядок
        chat_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=FIELD_HEIGHT, spacing=SMALL_SPACING)
        chat_row.add_widget(Label(text='Чат:', size_hint_x=0.25, text_size=(None, None), halign='left'))
        self.chat_spinner = Spinner(text='-- не завантажено --', values=['-- не завантажено --'], size_hint_x=0.55, font_size=dp(12))
        chat_row.add_widget(self.chat_spinner)
        self.load_chats_btn = Button(text='📥', size_hint_x=0.2, on_press=self.load_chats, font_size=dp(16))
        chat_row.add_widget(self.load_chats_btn)
        content.add_widget(chat_row)
        
        # Текст повідомлення - компактний багаторядковий
        content.add_widget(Label(text='Повідомлення:', size_hint_y=None, height=LABEL_HEIGHT, text_size=(None, None), halign='left'))
        self.msg_input = TextInput(text=self.cfg.get('text', ''), multiline=True, size_hint_y=None, height=dp(60), font_size=dp(13), padding=[dp(5), dp(5)])
        content.add_widget(self.msg_input)
        
        # Інтервал та Ліміт - в один рядок для компактності
        params_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=FIELD_HEIGHT, spacing=SMALL_SPACING)
        interval_col = BoxLayout(orientation='horizontal', size_hint_x=0.5, spacing=SMALL_SPACING)
        interval_col.add_widget(Label(text='Інт(с):', size_hint_x=0.4, text_size=(None, None), halign='left'))
        self.interval_input = TextInput(text=str(self.cfg.get('interval', 10)), multiline=False, size_hint_x=0.6, font_size=dp(14))
        interval_col.add_widget(self.interval_input)
        params_row.add_widget(interval_col)
        
        limit_col = BoxLayout(orientation='horizontal', size_hint_x=0.5, spacing=SMALL_SPACING)
        limit_col.add_widget(Label(text='К-сть:', size_hint_x=0.4, text_size=(None, None), halign='left'))
        self.limit_input = TextInput(text=str(self.cfg.get('limit', 1)), multiline=False, size_hint_x=0.6, font_size=dp(14), hint_text='0=1 раз, N=N раз')
        limit_col.add_widget(self.limit_input)
        params_row.add_widget(limit_col)
        content.add_widget(params_row)
        
        # Розклад - компактний
        content.add_widget(Label(text='Розклад (HH:MM):', size_hint_y=None, height=LABEL_HEIGHT, text_size=(None, None), halign='left'))
        self.schedule_input = TextInput(text=self.cfg.get('schedule_times', ''), multiline=False, size_hint_y=None, height=FIELD_HEIGHT, font_size=dp(13))
        content.add_widget(self.schedule_input)
        
        # Чекбокс повторення - компактний
        repeat_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30), spacing=SMALL_SPACING)
        self.repeat_checkbox = CheckBox(active=self.cfg.get('repeat_daily', True), size_hint_x=0.1)
        repeat_row.add_widget(self.repeat_checkbox)
        repeat_row.add_widget(Label(text='Повторювати щодня', size_hint_x=0.9, text_size=(None, None), halign='left', font_size=dp(12)))
        content.add_widget(repeat_row)
        
        # Кнопки - компактні, більші для зручності
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=BTN_HEIGHT, spacing=dp(5))
        self.start_btn = Button(text='🚀 СТАРТ', on_press=self.start_client, size_hint_x=0.5, font_size=dp(16), bold=True)
        self.stop_btn = Button(text='⏹️ СТОП', on_press=self.stop_client, size_hint_x=0.5, font_size=dp(16), bold=True)
        btn_row.add_widget(self.start_btn)
        btn_row.add_widget(self.stop_btn)
        content.add_widget(btn_row)
        
        # Логи - адаптивний розмір (більше в горизонтальному режимі)
        content.add_widget(Label(text='Логи:', size_hint_y=None, height=LABEL_HEIGHT, text_size=(None, None), halign='left'))
        log_height = dp(150) if not self._is_landscape() else dp(100)
        log_scroll = ScrollView(size_hint_y=None, height=log_height)
        self.log_label = Label(text='', text_size=(None, None), halign='left', valign='top', size_hint_y=None, font_size=dp(11))
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        log_scroll.add_widget(self.log_label)
        content.add_widget(log_scroll)
        
        # Довідка - компактна кнопка
        help_btn = Button(text='❓ Довідка', size_hint_y=None, height=dp(35), on_press=self.show_help, font_size=dp(12))
        content.add_widget(help_btn)
        
        scroll.add_widget(content)
        self.add_widget(scroll)
        
        # Зберігаємо посилання на scroll для можливої адаптації
        self.scroll_view = scroll
        self.content_layout = content
    
    def log(self, text):
        """Додавання логу (thread-safe)"""
        Clock.schedule_once(lambda dt: self._log_mainthread(text), 0)
    
    @mainthread
    def _log_mainthread(self, text):
        """Оновлення логів у головному потоці"""
        current = self.log_label.text
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_label.text = f"{current}[{timestamp}] {text}\n"
        # Скрол до кінця
        for child in self.log_label.parent.children:
            if isinstance(child, ScrollView):
                child.scroll_y = 0
    
    def show_error(self, message):
        """Показати помилку"""
        self.log(f"❌ {message}")
        error_label = Label(text=message, text_size=(Window.width * 0.7, None), halign='center', valign='middle')
        popup = Popup(title='Помилка', content=error_label, size_hint=(0.85, 0.35))
        popup.open()
    
    def show_help(self, *args):
        """Показати довідку"""
        help_text = """Довідка — Telegram User Bot

• Інтервал: повідомлення (через кому) надсилаються по колу кожні N секунд.
• Кількість: 0 = відправити один раз, N > 0 = відправити N повідомлень.
• Розклад: підтримує HH:MM, DD.MM HH:MM, DD.MM.YYYY HH:MM, сьогодні/завтра HH:MM.
• Токени стікерів: [[emoji:file.webp]] (файли в папці emojis/).
• Поворот екрана: підтримується вертикальний та горизонтальний режими.
• Авторизація зберігається між запусками - не потрібно вводити код щоразу.
"""
        help_label = Label(text=help_text, text_size=(Window.width * 0.85, None), halign='left', valign='top', font_size=dp(13))
        scroll_help = ScrollView()
        scroll_help.add_widget(help_label)
        popup = Popup(title='Довідка', content=scroll_help, size_hint=(0.9, 0.65))
        popup.open()
    
    def _show_input_dialog(self, title, prompt, callback):
        """Показати діалог введення (адаптований для смартфона)"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        prompt_label = Label(text=prompt, text_size=(Window.width * 0.7, None), halign='center', font_size=dp(13))
        input_field = TextInput(multiline=False, size_hint_y=None, height=dp(45), font_size=dp(15))
        btn_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=dp(5))
        
        def on_ok(*args):
            popup.dismiss()
            callback(input_field.text)
        
        def on_cancel(*args):
            popup.dismiss()
            callback(None)
        
        ok_btn = Button(text='OK', on_press=on_ok, font_size=dp(15), bold=True)
        cancel_btn = Button(text='Скасувати', on_press=on_cancel, font_size=dp(15))
        btn_row.add_widget(ok_btn)
        btn_row.add_widget(cancel_btn)
        content.add_widget(prompt_label)
        content.add_widget(input_field)
        content.add_widget(btn_row)
        
        popup = Popup(title=title, content=content, size_hint=(0.85, 0.35))
        popup.open()
        input_field.focus = True
    
    async def _ensure_login(self, api_id, api_hash):
        """Авторизація (async)"""
        if self.client is None:
            self.client = TelegramClient(SESSION_PATH, api_id, api_hash)
        
        await self.client.connect()
        if await self.client.is_user_authorized():
            return
        
        # Запит номера телефону
        phone_future = asyncio.Future()
        def set_phone(text):
            phone_future.set_result(text)
        
        Clock.schedule_once(lambda dt: self._show_input_dialog("Авторизація", "Введіть номер (+380...):", set_phone), 0)
        phone = await phone_future
        if not phone:
            raise RuntimeError("Скасовано")
        
        try:
            await self.client.send_code_request(phone)
        except PhoneNumberInvalidError:
            raise RuntimeError("Некоректний номер")
        
        # Запит коду
        while True:
            code_future = asyncio.Future()
            def set_code(text):
                code_future.set_result(text)
            
            Clock.schedule_once(lambda dt: self._show_input_dialog("Код", "Введіть код:", set_code), 0)
            code = await code_future
            if not code:
                raise RuntimeError("Скасовано")
            
            try:
                await self.client.sign_in(phone=phone, code=code)
                break
            except PhoneCodeExpiredError:
                self.log("Код прострочено, надсилаю новий...")
                await self.client.send_code_request(phone)
            except PhoneCodeInvalidError:
                self.log("Невірний код, спробуйте ще раз.")
            except SessionPasswordNeededError:
                # 2FA
                pwd_future = asyncio.Future()
                def set_pwd(text):
                    pwd_future.set_result(text)
                
                Clock.schedule_once(lambda dt: self._show_input_dialog("2FA", "Пароль 2FA:", set_pwd), 0)
                pwd = await pwd_future
                if not pwd:
                    raise RuntimeError("Скасовано")
                await self.client.sign_in(password=pwd)
                break
    
    def load_chats(self, *args):
        """Завантажити список чатів"""
        try:
            api_id = int(self.api_id_input.text.strip())
            api_hash = self.api_hash_input.text.strip()
        except Exception:
            self.show_error("Введіть коректні API ID та HASH!")
            return
        
        if self.client is None:
            self.client = TelegramClient(SESSION_PATH, api_id, api_hash)
        
        async def fetch_chats():
            try:
                # Зберігаємо API credentials перед авторизацією
                save_config({
                    "api_id": api_id,
                    "api_hash": api_hash,
                    **{k: v for k, v in self.cfg.items() if k not in ['api_id', 'api_hash']}
                })
                self.cfg = load_config()  # Оновлюємо конфігурацію
                
                await self._ensure_login(api_id, api_hash)
                dialogs = await self.client.get_dialogs()
                self.chat_map = {d.name: d.id for d in dialogs}
                chats_list = list(self.chat_map.keys()) or ["(нема чатів)"]
                
                Clock.schedule_once(lambda dt: self._update_chats_list(chats_list), 0)
                self.log(f"✅ Завантажено {len(chats_list)} чатів")
            except Exception as e:
                self.log(f"❌ Помилка: {e}")
        
        asyncio.run_coroutine_threadsafe(fetch_chats(), self.loop)
    
    @mainthread
    def _update_chats_list(self, chats_list):
        """Оновити список чатів у головному потоці"""
        self.chat_spinner.values = chats_list
        if chats_list:
            # Відновлюємо вибраний чат з конфігурації
            saved_chat = self.cfg.get('chat', '')
            if saved_chat in chats_list:
                self.chat_spinner.text = saved_chat
            else:
                self.chat_spinner.text = chats_list[0]
    
    def stop_client(self, *args):
        """Зупинити розсилку"""
        self.stop_flag = True
        self.log("⏹️ Сигнал зупинки...")
    
    def start_client(self, *args):
        """Запустити розсилку"""
        try:
            api_id = int(self.api_id_input.text.strip())
            api_hash = self.api_hash_input.text.strip()
            chat_name = self.chat_spinner.text
            chat = self.chat_map.get(chat_name, None)
            text_raw = self.msg_input.text.strip()
            interval = int(self.interval_input.text.strip())
            limit = int(self.limit_input.text.strip())
            schedule_times = self.schedule_input.text.strip()
            repeat_daily = self.repeat_checkbox.active
            
            if not chat:
                self.show_error("Виберіть чат!")
                return
            if not text_raw:
                self.show_error("Введіть текст!")
                return
            if interval <= 0:
                self.show_error("Інтервал має бути > 0!")
                return
            
            # Перевірка limit: 0 = один раз, >0 = N повідомлень
            if limit < 0:
                self.show_error("Кількість має бути 0 або більше!")
                return
            
            messages = [m.strip() for m in text_raw.split(",") if m.strip()]
            daily_times, absolute_times = _parse_schedule_tokens(schedule_times)
            
            # Зберігаємо всю конфігурацію (включаючи API credentials)
            save_config({
                "api_id": api_id,
                "api_hash": api_hash,
                "text": text_raw,
                "interval": interval,
                "limit": limit,
                "schedule_times": schedule_times,
                "repeat_daily": repeat_daily,
                "chat": chat_name
            })
            self.cfg = load_config()  # Оновлюємо конфігурацію
            
            if self.client is None:
                self.client = TelegramClient(SESSION_PATH, api_id, api_hash)
            
            async def start_task():
                try:
                    self.stop_flag = False
                    
                    # Перевіряємо чи вже авторизовано (щоб не питати код щоразу)
                    if not await self.client.is_user_authorized():
                        await self._ensure_login(api_id, api_hash)
                    
                    me = await self.client.get_me()
                    uname = f"@{me.username}" if getattr(me, "username", None) else ""
                    self.log(f"✅ Авторизація успішна! {me.first_name} {uname}")
                    
                    if daily_times or absolute_times:
                        mode = "щодня" if repeat_daily else "один раз"
                        self.log(f"🕒 Розклад: daily={daily_times} | once={absolute_times} | {mode}")
                        asyncio.create_task(
                            send_by_schedule(self.client, chat, messages, daily_times, absolute_times,
                                           repeat_daily, self.log, lambda: self.stop_flag)
                        )
                    else:
                        # Логування в залежності від limit
                        if limit == 0:
                            self.log(f"📤 Відправляю повідомлення один раз (limit=0)...")
                        else:
                            self.log(f"🚀 Починаю розсилку з інтервалом {interval} с (кількість: {limit})")
                        asyncio.create_task(
                            send_periodic(self.client, chat, messages, interval, limit, self.log, lambda: self.stop_flag)
                        )
                except Exception as e:
                    self.log(f"❌ Помилка: {e}")
            
            asyncio.run_coroutine_threadsafe(start_task(), self.loop)
            
        except Exception as e:
            self.show_error(str(e))
    
    def on_closing(self):
        """При закритті"""
        async def close_client():
            if self.client:
                await self.client.disconnect()
        try:
            asyncio.run_coroutine_threadsafe(close_client(), self.loop).result(timeout=2)
        except Exception:
            pass
        try:
            self.loop.stop()
        except Exception:
            pass


if __name__ == '__main__':
    # Налаштування Window для смартфона
    if platform != 'android':
        # Для тестування на Windows - можна встановити розмір як смартфон
        # Window.size = (360, 640)  # Розкоментуйте для тестування
        pass
    
    TelegramUserApp().run()

