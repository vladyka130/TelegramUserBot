import sys
import os
import re
import json
import queue
import asyncio
import threading
import platform
import tkinter as tk
import tkinter.messagebox as mbox
from tkinter import simpledialog
from datetime import datetime, timedelta

import customtkinter as ctk
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError,
    PhoneCodeExpiredError, PhoneNumberInvalidError
)

# --- Рекомендована політика циклу подій для Windows (стабільніше у .exe) ---
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# --- SSL сертифікати (для стабільної мережі у зібраному .exe) ---
try:
    import certifi
    os.environ["SSL_CERT_FILE"] = certifi.where()
except Exception:
    pass

# ---------------- Константи та підготовка ----------------
CONFIG_FILE = "config.json"
EMOJI_DIR = "emojis"

# де зберігати .session стабільно (не залежить від місця exe)
APPDIR = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "TelegramUserSender")
os.makedirs(APPDIR, exist_ok=True)
SESSION_PATH = os.path.join(APPDIR, "my_account")  # БЕЗ .session — Telethon додасть

if not os.path.exists(EMOJI_DIR):
    os.makedirs(EMOJI_DIR)


# --- 📏 Адаптація DPI ---
def enable_dpi_awareness():
    system = platform.system()
    if system == "Windows":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass


def auto_scale():
    try:
        tmp = tk.Tk()
        dpi = tmp.winfo_fpixels('1i')
        tmp.destroy()
        scale = dpi / 96
        return round(scale, 2)
    except Exception:
        return 1.0


enable_dpi_awareness()
ctk.set_widget_scaling(auto_scale())
ctk.set_window_scaling(auto_scale())


# ---------------- Допоміжне: відправити ОДНЕ повідомлення ----------------
async def _send_one_message(client, chat, msg_text, log_callback):
    """
    msg_text може містити токени [[emoji:FILE.webp]].
    Відправляє спершу текст (якщо є), далі кожен файл окремо.
    """
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


# ---------------- Розбір розкладу ----------------
def _parse_schedule_tokens(text: str):
    """
    Повертає (daily_times: list['HH:MM'], absolute_times: list[datetime]).
    Підтримується (через кому):
      - HH:MM
      - DD.MM HH:MM  (поточний рік)
      - DD.MM.YYYY HH:MM
      - YYYY-MM-DD HH:MM
      - сьогодні HH:MM / завтра HH:MM / післязавтра HH:MM
    """
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

        # ключові слова
        m = re.match(r"^(сьогодні|завтра|післязавтра)\s+(\d{1,2}):(\d{2})$", low)
        if m:
            kw, hh, mm = m.groups()
            hh, mm = int(hh), int(mm)
            base = now.replace(second=0, microsecond=0)
            if kw == "сьогодні":
                dt = base.replace(hour=hh, minute=mm)
            elif kw == "завтра":
                dt = (base + timedelta(days=1)).replace(hour=hh, minute=mm)
            else:  # післязавтра
                dt = (base + timedelta(days=2)).replace(hour=hh, minute=mm)
            absolute_times.append(dt)
            continue

        # YYYY-MM-DD HH:MM
        m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})$", token)
        if m:
            y, mo, d, h, mi = map(int, m.groups())
            absolute_times.append(datetime(y, mo, d, h, mi, 0, 0))
            continue

        # DD.MM.YYYY HH:MM
        m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})$", token)
        if m:
            d, mo, y, h, mi = map(int, m.groups())
            absolute_times.append(datetime(y, mo, d, h, mi, 0, 0))
            continue

        # DD.MM HH:MM  (поточний рік)
        m = re.match(r"^(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{2})$", token)
        if m:
            d, mo, h, mi = map(int, m.groups())
            absolute_times.append(datetime(now.year, mo, d, h, mi, 0, 0))
            continue

        # HH:MM (щодня)
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


# ---------------- Інтервальна розсилка (по колу) ----------------
async def send_periodic(client, chat, messages, interval, limit, log_callback, stop_check):
    if not messages:
        log_callback("❌ Немає повідомлень для відправки.")
        return
    count = 0
    idx = 0
    n = len(messages)
    while True:
        if stop_check():
            log_callback("⏹️ Відправку зупинено користувачем.")
            break
        if limit and count >= limit:
            log_callback(f"⏹️ Відправка завершена (надіслано {count} повідомлень).")
            break
        msg = messages[idx % n]
        idx += 1
        await _send_one_message(client, chat, msg, log_callback)
        count += 1
        await asyncio.sleep(interval)


# ---------------- Розсилка за розкладом ----------------
async def send_by_schedule(client, chat, messages, daily_times, absolute_times, repeat_daily, log_callback, stop_check):
    if not messages:
        log_callback("❌ Немає повідомлень для відправки.")
        return

    sent_today = set()        # HH:MM → вже відправляли сьогодні
    sent_daily_once = set()   # HH:MM → уже відправлено (якщо repeat_daily=False)
    fired_abs = set()         # 'YYYY-MM-DD HH:MM' → разові події

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

        # щоденні
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

        # разові
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

        # скидання щоденних міток опівночі
        if current_min == "00:00":
            sent_today.clear()

        await asyncio.sleep(30)


# ---------------- Загальні хелпери ----------------
def start_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def add_paste_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Вставити", command=lambda: widget.event_generate("<<Paste>>"))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-3>", show_menu)


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


# ---------------- Головний GUI ----------------
class TelegramUserGUI(ctk.CTk):
    HELP_TEXT = """Довідка — Telegram User Sender (Telethon)

Розробник: Vladyka
Дата: 05.10.2025

• Інтервал: повідомлення (кілька, через кому) надсилаються по колу кожні N секунд.
• Розклад: підтримує щоденні години HH:MM (з/без повторення щодня) та разові події з датою:
  - HH:MM
  - DD.MM HH:MM
  - DD.MM.YYYY HH:MM
  - YYYY-MM-DD HH:MM
  - сьогодні/завтра/післязавтра HH:MM
• Токени стікерів у тексті: [[emoji:Назва.webp]] (файли в папці emojis/).
• Сесія Telegram зберігається в %LOCALAPPDATA%\\TelegramUserSender\\my_account.session.
• Перша авторизація проходить через вікна (номер, код, 2FA) — без консолі.
"""

    def __init__(self):
        super().__init__()
        self.title("Telegram User Sender (Telethon)")
        self.geometry("500x525")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=start_async_loop, args=(self.loop,), daemon=True)
        self.loop_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client = None
        self.stop_flag = False
        self.chat_map = {}
        self.cfg = load_config()

        self.build_ui()
        # F1 = довідка
        self.bind("<F1>", lambda e: self.show_help())

    # ----- вікно довідки -----
    def show_help(self):
        win = ctk.CTkToplevel(self)
        win.title("Довідка")
        win.geometry("720x560")
        # центруємо
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 720) // 2
        y = self.winfo_y() + (self.winfo_height() - 560) // 2
        win.geometry(f"720x560+{x}+{y}")
        win.grab_set()
        txt = ctk.CTkTextbox(win, width=700, height=500, corner_radius=6, wrap="word")
        txt.pack(padx=10, pady=(10, 8), fill="both", expand=True)
        txt.insert("1.0", self.HELP_TEXT)
        txt.configure(state="disabled")
        btn_row = ctk.CTkFrame(win)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(btn_row, text="Закрити", width=100, fg_color="#134e37",
                      corner_radius=1, command=win.destroy).pack(side="right")

    # ----- побудова UI -----
    def build_ui(self):
        self.api_id_label = ctk.CTkLabel(self, text="API ID:")
        self.api_id_label.place(x=20, y=10)

        self.api_id_entry = ctk.CTkEntry(self, width=400, corner_radius=1, border_width=1, border_color="#134e37")
        self.api_id_entry.insert(0, str(self.cfg.get("api_id", "")))
        self.api_id_entry.place(x=90, y=10)
        add_paste_menu(self.api_id_entry)

        self.api_hash_label = ctk.CTkLabel(self, text="API HASH:")
        self.api_hash_label.place(x=20, y=45)
        self.api_hash_entry = ctk.CTkEntry(self, width=400, corner_radius=1, border_width=1, border_color="#134e37")
        self.api_hash_entry.insert(0, self.cfg.get("api_hash", ""))
        self.api_hash_entry.place(x=90, y=45)
        add_paste_menu(self.api_hash_entry)

        self.chat_label = ctk.CTkLabel(self, text="Вибери чат/контакт:")
        self.chat_label.place(x=20, y=80)
        self.chat_var = ctk.StringVar(value="-- ще не завантажено --")
        self.chat_menu = ctk.CTkOptionMenu(self, variable=self.chat_var, values=["-- ще не завантажено --"],
                                           corner_radius=1, width=320, button_color="#134e37",
                                           fg_color="#134e37", anchor="center")
        self.chat_menu.place(x=170, y=80)

        self.load_btn = ctk.CTkButton(self, text="-- Завантажити список чатів --", command=self.load_chats,
                                      width=320, fg_color="#134e37", corner_radius=1)
        self.load_btn.place(x=170, y=110)

        self.msg_label = ctk.CTkLabel(self, text="Текст повідомлення:")
        self.msg_label.place(x=35, y=145)
        self.msg_entry = ctk.CTkEntry(self, width=320, corner_radius=1, border_width=1, border_color="#134e37")
        self.msg_entry.insert(0, self.cfg.get("text", ""))
        self.msg_entry.place(x=170, y=145)
        add_paste_menu(self.msg_entry)

        self.interval_label = ctk.CTkLabel(self, text="Інтервал (секунди):")
        self.interval_label.place(x=45, y=175)
        self.interval_entry = ctk.CTkEntry(self, width=320, corner_radius=1, border_width=1, border_color="#134e37")
        self.interval_entry.insert(0, str(self.cfg.get("interval", 10)))
        self.interval_entry.place(x=170, y=175)
        add_paste_menu(self.interval_entry)

        self.limit_label = ctk.CTkLabel(self, text="К-сть (0 = безкінечно):")
        self.limit_label.place(x=30, y=205)
        self.limit_entry = ctk.CTkEntry(self, width=320, corner_radius=1, border_width=1, border_color="#134e37")
        self.limit_entry.insert(0, str(self.cfg.get("limit", 0)))
        self.limit_entry.place(x=170, y=205)
        add_paste_menu(self.limit_entry)

        self.start_btn = ctk.CTkButton(self, text="🚀 Старт", width=238, fg_color="#134e37", corner_radius=1,
                                       command=self.start_client)
        self.start_btn.place(x=10, y=245)

        self.stop_btn = ctk.CTkButton(self, text="⏹️ Стоп", width=238, command=self.stop_client, fg_color="red",
                                      corner_radius=1)
        self.stop_btn.place(x=252, y=245)

        self.log_box = ctk.CTkTextbox(self, width=480, height=150, corner_radius=1)
        self.log_box.place(x=10, y=280)

        # --- поле для часу/дат ---
        self.schedule_label = ctk.CTkLabel(self, text="Час/дати (HH:MM або ДД.MM[.РРРР] HH:MM, через кому):")
        self.schedule_label.place(x=10, y=435)
        self.schedule_entry = ctk.CTkEntry(self, width=480, corner_radius=1, border_width=1, border_color="#134e37")
        self.schedule_entry.insert(0, self.cfg.get("schedule_times", ""))
        self.schedule_entry.place(x=10, y=460)

        # --- чекбокс ---
        self.repeat_var = tk.BooleanVar(value=self.cfg.get("repeat_daily", True))
        self.repeat_checkbox = ctk.CTkCheckBox(
            self, text="Повторювати щодня (для HH:MM)",
            variable=self.repeat_var, corner_radius=1, border_width=1, border_color="#134e37"
        )
        self.repeat_checkbox.place(x=10, y=495)

        # --- кнопка довідки ---
        self.help_btn = ctk.CTkButton(
            self, text="❓ Довідка", width=80, fg_color="#134e37",
            corner_radius=1, height=25, command=self.show_help
        )
        self.help_btn.place(x=410, y=495)

    # ----- лог -----
    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    # ----- модальний input у головному потоці -----
    def _ask_on_main(self, title, prompt, show=None):
        q = queue.Queue()

        def _do():
            ans = simpledialog.askstring(title, prompt, parent=self, show=show)
            q.put(ans)

        self.after(0, _do)
        return q.get()

    # ----- асинхронна авторизація без консолі -----
    async def _ensure_login(self, api_id, api_hash):
        if self.client is None:
            self.client = TelegramClient(SESSION_PATH, api_id, api_hash)

        await self.client.connect()
        if await self.client.is_user_authorized():
            return

        phone = self._ask_on_main("Авторизація", "Введіть номер у форматі +380...")
        if not phone:
            raise RuntimeError("Скасовано введення номера.")
        try:
            await self.client.send_code_request(phone)
        except PhoneNumberInvalidError:
            raise RuntimeError("Некоректний номер телефону.")

        while True:
            code = self._ask_on_main("Код підтвердження", "Введіть код із Telegram:")
            if not code:
                raise RuntimeError("Скасовано введення коду.")
            try:
                await self.client.sign_in(phone=phone, code=code)
                break
            except PhoneCodeExpiredError:
                self.log("Код прострочено, надсилаю новий...")
                await self.client.send_code_request(phone)
            except PhoneCodeInvalidError:
                self.log("Невірний код, спробуйте ще раз.")
            except SessionPasswordNeededError:
                pwd = self._ask_on_main("Пароль 2FA", "Введіть пароль 2FA:", show="*")
                if not pwd:
                    raise RuntimeError("Скасовано введення 2FA.")
                await self.client.sign_in(password=pwd)
                break

    # ----- події -----
    def show_error(self, message: str):
        self.log("❌ " + message)
        try:
            mbox.showerror("Помилка", message)
        except Exception:
            pass

    def stop_client(self):
        self.stop_flag = True
        self.log("⏹️ Сигнал зупинки відправки...")

    def load_chats(self):
        try:
            api_id = int(self.api_id_entry.get().strip())
            api_hash = self.api_hash_entry.get().strip()
        except Exception:
            self.show_error("Введи коректні API ID та HASH для завантаження чатів!")
            return

        if self.client is None:
            self.client = TelegramClient(SESSION_PATH, api_id, api_hash)

        async def fetch_chats():
            try:
                await self._ensure_login(api_id, api_hash)
                dialogs = await self.client.get_dialogs()
                self.chat_map = {d.name: d.id for d in dialogs}
                chats_list = list(self.chat_map.keys()) or ["(нема чатів)"]
                self.chat_menu.configure(values=chats_list)
                self.chat_var.set(chats_list[0])
                self.log(f"✅ Завантажено {len(chats_list)} чатів")
            except Exception as e:
                self.show_error(f"Не вдалося завантажити чати: {e}")

        asyncio.run_coroutine_threadsafe(fetch_chats(), self.loop)

    def start_client(self):
        try:
            api_id = int(self.api_id_entry.get().strip())
        except ValueError:
            self.show_error("API ID має бути числом!")
            return

        api_hash = self.api_hash_entry.get().strip()
        if not api_hash:
            self.show_error("Поле API HASH порожнє!")
            return

        chat_name = self.chat_var.get()
        chat = self.chat_map.get(chat_name, None)
        if not chat:
            self.show_error("Не вибрано жоден чат!")
            return

        text_raw = self.msg_entry.get().strip()
        if not text_raw:
            self.show_error("Поле тексту повідомлення порожнє!")
            return

        # список повідомлень через кому
        messages = [m.strip() for m in text_raw.split(",") if m.strip()]
        if not messages:
            self.show_error("Не вдалося сформувати список повідомлень (перевір розділення комами).")
            return

        try:
            interval = int(self.interval_entry.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            self.show_error("Інтервал має бути додатним числом!")
            return

        try:
            limit = int(self.limit_entry.get().strip())
            if limit < 0:
                raise ValueError
        except ValueError:
            self.show_error("Кількість відправок має бути 0 або більше!")
            return

        # розбір розкладу
        times_raw = self.schedule_entry.get().strip()
        try:
            daily_times, absolute_times = _parse_schedule_tokens(times_raw)
        except ValueError as e:
            self.show_error(str(e))
            return

        repeat_daily = self.repeat_var.get()

        save_config({
            "api_id": api_id,
            "api_hash": api_hash,
            "chat": chat_name,
            "text": text_raw,
            "interval": interval,
            "limit": limit,
            "schedule_times": times_raw,
            "repeat_daily": repeat_daily
        })

        if self.client is None:
            self.client = TelegramClient(SESSION_PATH, api_id, api_hash)

        async def start_task():
            try:
                self.stop_flag = False
                await self._ensure_login(api_id, api_hash)
                me = await self.client.get_me()
                uname = f"@{me.username}" if getattr(me, "username", None) else ""
                self.log(f"✅ Авторизація успішна! Ви увійшли як {me.first_name} {uname}")

                if daily_times or absolute_times:
                    mode = "щодня" if repeat_daily else "один раз (для HH:MM)"
                    daily_txt = ", ".join(daily_times) if daily_times else "—"
                    abs_txt = ", ".join(dt.strftime("%d.%m.%Y %H:%M") for dt in absolute_times) if absolute_times else "—"
                    self.log(f"🕒 Розклад: daily={daily_txt} | once={abs_txt} | режим={mode}")
                    # ВАЖЛИВО: Python 3.11 — використовуємо create_task (без loop=)
                    asyncio.create_task(
                        send_by_schedule(self.client, chat, messages, daily_times, absolute_times,
                                         repeat_daily, self.log, lambda: self.stop_flag)
                    )
                else:
                    self.log(f"🚀 Починаю розсилку з інтервалом {interval} с")
                    asyncio.create_task(
                        send_periodic(self.client, chat, messages, interval, limit, self.log, lambda: self.stop_flag)
                    )
            except Exception as e:
                self.show_error(f"Помилка при запуску клієнта: {e}")

        asyncio.run_coroutine_threadsafe(start_task(), self.loop)

    def on_closing(self):
        async def close_client():
            if self.client:
                await self.client.disconnect()
        try:
            asyncio.run_coroutine_threadsafe(close_client(), self.loop).result()
        except Exception:
            pass
        try:
            self.loop.stop()
        except Exception:
            pass
        self.destroy()


# --- запуск ---
if __name__ == "__main__":
    app = TelegramUserGUI()
    app.mainloop()
