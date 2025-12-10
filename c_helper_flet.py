# c_helper_flet.py
# Версія для flet==0.70.0.dev6370 (оновлена, стабільна)

import flet as ft
import asyncio
import threading
import time
import sqlite3
from datetime import datetime
from collections import deque
from queue import Queue, Empty
import threading
import pyperclip


DB_PATH = "freq_db.sqlite"
MAX_GUI_ROWS = 15
POLL_INTERVAL_SEC = 0.5

event_q = Queue()
stop_flag = threading.Event()
all_events = deque(maxlen=500)

# === глобальні посилання ===
FOCUS_COLOR_BY_FREQ = {}  # freq -> color
HISTORY_LIST: ft.ListView | None = None
ACTIVE_ELEMENTS = {"focus_freq_field": None}  # для вставлення частоти у вікно фокусу


# ---------- SQLite ----------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS focus_freqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                freq   TEXT NOT NULL,
                reason TEXT NOT NULL,
                color  TEXT NOT NULL DEFAULT '#ff3333'
            )
        """)


def get_all_focuses():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT id, freq, reason, color FROM focus_freqs ORDER BY id DESC"
        ).fetchall()


def add_focus(freq, reason, color):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO focus_freqs (freq, reason, color) VALUES (?, ?, ?)",
            (freq, reason, color),
        )
        conn.commit()


def update_focus(id_, reason, color):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE focus_freqs SET reason=?, color=? WHERE id=?",
            (reason, color, id_),
        )
        conn.commit()


def remove_focus(id_):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM focus_freqs WHERE id=?", (id_,))
        conn.commit()


# ---------- Допоміжні ----------
def apply_focus_to_history(history: ft.ListView):
    """Перефарбовує рамки вже відрендерених рядків історії згідно з FOCUS_COLOR_BY_FREQ."""
    if not history:
        return
    changed = False
    for c in history.controls:
        if isinstance(c, ft.Container) and isinstance(c.data, dict) and "freq" in c.data:
            freq = c.data.get("freq")
            col = FOCUS_COLOR_BY_FREQ.get(freq)
            new_border = ft.Border.all(2, col) if col else ft.Border.all(1, "#444444")
            if getattr(c, "border", None) != new_border:
                c.border = new_border
                changed = True
    if changed:
        history.update()


def sync_focus_map_and_repaint():
    """Оновлюємо мапу кольорів фокусів і миттєво перефарбовуємо історію."""
    global FOCUS_COLOR_BY_FREQ, HISTORY_LIST
    FOCUS_COLOR_BY_FREQ = {freq: color for (_, freq, _, color) in get_all_focuses()}
    if HISTORY_LIST:
        apply_focus_to_history(HISTORY_LIST)


# ---------- Демонстраційний потік моніторингу ----------
def fake_poll_loop():
    """імітація отримання частот кожні 0.5 сек"""
    while not stop_flag.is_set():
        now = datetime.now().strftime("%H:%M:%S")
        freq = f"{round(150 + (time.time() % 50), 3)}"
        event = {"time": now, "freq": freq, "dur": "00:12", "src": "SRC-1"}
        event_q.put(event)
        time.sleep(POLL_INTERVAL_SEC)


# ---------- Вікно "Робота з фокусом" ----------
def open_focus_window(page: ft.Page):
    freq_input = ft.TextField(label="Частота", width=120)
    ACTIVE_ELEMENTS["focus_freq_field"] = freq_input  # <=== збережемо посилання

    reason_input = ft.TextField(label="Причина", width=260)

    available_colors = [
        "#ff3333", "#ff9933", "#ffff33", "#33ff33",
        "#33ffff", "#3399ff", "#9933ff", "#ff66cc"
    ]
    selected_color = {"value": "#ff3333"}

    def select_color(e, color):
        selected_color["value"] = color
        for btn in color_buttons.controls:
            btn.border = ft.Border.all(2, "#333333")
        e.control.border = ft.Border.all(2, "white")
        page.update()

    color_buttons = ft.Row(
        [
            ft.Container(
                width=24,
                height=24,
                bgcolor=color,
                border_radius=6,
                border=ft.Border.all(2, "#333333"),
                on_click=lambda e, c=color: select_color(e, c),
            )
            for color in available_colors
        ],
        spacing=6,
    )
    color_buttons.controls[0].border = ft.Border.all(2, "white")

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Частота")),
            ft.DataColumn(ft.Text("Причина")),
            ft.DataColumn(ft.Text("Колір")),
            ft.DataColumn(ft.Text("Дії")),
        ],
        rows=[],
        column_spacing=10,
    )

    edit_section = ft.Container(visible=False)

    def refresh_table():
        table.rows.clear()
        for (id_, freq, reason, color) in get_all_focuses():
            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(id_))),
                        ft.DataCell(ft.Text(freq)),
                        ft.DataCell(ft.Text(reason)),
                        ft.DataCell(
                            ft.Container(width=18, height=18, bgcolor=color,
                                         border_radius=9, border=ft.Border.all(1, "#555555"))
                        ),
                        ft.DataCell(
                            ft.Row(
                                [
                                    ft.TextButton("✏️", on_click=lambda e, i=id_: open_edit_section(i)),
                                    ft.TextButton("🗑️", on_click=lambda e, i=id_: (
                                        remove_focus(i),
                                        refresh_table(),
                                        sync_focus_map_and_repaint(),
                                        page.update(),
                                    )),
                                ],
                                spacing=6,
                            )
                        ),
                    ]
                )
            )
        page.update()

    def add_new_focus(e):
        f = (freq_input.value or "").strip()
        r = (reason_input.value or "").strip()
        c = selected_color["value"]
        if not f or not r:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Заповніть частоту і причину!"))
            page.snack_bar.open = True
            page.update()
            return
        add_focus(f, r, c)
        freq_input.value, reason_input.value = "", ""
        selected_color["value"] = available_colors[0]
        for btn in color_buttons.controls:
            btn.border = ft.Border.all(2, "#333333")
        color_buttons.controls[0].border = ft.Border.all(2, "white")

        refresh_table()
        sync_focus_map_and_repaint()
        page.snack_bar = ft.SnackBar(ft.Text("✅ Фокус додано!"))
        page.snack_bar.open = True
        page.update()

    def open_edit_section(focus_id: int):
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute("SELECT freq, reason, color FROM focus_freqs WHERE id=?", (focus_id,)).fetchone()
        if not row:
            return
        freq, reason, color = row

        reason_field = ft.TextField(label="Причина", value=reason, width=300)
        selected_color["value"] = color

        def choose_edit_color(e, col):
            selected_color["value"] = col
            for btn in edit_colors.controls:
                btn.border = ft.Border.all(2, "#333333")
            e.control.border = ft.Border.all(2, "white")
            page.update()

        edit_colors = ft.Row(
            [
                ft.Container(width=24, height=24, bgcolor=col, border_radius=6,
                             border=ft.Border.all(2, "#333333"),
                             on_click=lambda e, c=col: choose_edit_color(e, c))
                for col in available_colors
            ],
            spacing=6,
        )
        for btn in edit_colors.controls:
            if btn.bgcolor == color:
                btn.border = ft.Border.all(2, "white")
                break

        def save_changes(e):
            update_focus(focus_id, reason_field.value, selected_color["value"])
            edit_section.visible = False
            refresh_table()
            sync_focus_map_and_repaint()
            page.snack_bar = ft.SnackBar(ft.Text("✅ Фокус оновлено!"))
            page.snack_bar.open = True
            page.update()

        def cancel_edit(e):
            edit_section.visible = False
            page.update()

        edit_section.content = ft.Container(
            bgcolor="#2a2a2a",
            padding=15,
            border_radius=8,
            content=ft.Column(
                [
                    ft.Text(f"Редагування фокусу: {freq}", size=16, weight=ft.FontWeight.BOLD),
                    reason_field,
                    edit_colors,
                    ft.Row(
                        [ft.Button("💾 Зберегти", on_click=save_changes),
                         ft.Button("❌ Скасувати", on_click=cancel_edit)],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=10,
            ),
        )
        edit_section.visible = True
        page.update()

    refresh_table()

    focus_view = ft.Container(
        bgcolor="#1E1E1E",
        padding=20,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=25, color="#00000066"),
        content=ft.Column(
            [
                ft.Text("🎯 Робота з фокусом", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([freq_input, reason_input, color_buttons,
                        ft.Button("➕ Додати", on_click=add_new_focus)],
                       alignment=ft.MainAxisAlignment.START, spacing=10),
                ft.Divider(),
                table,
                ft.Divider(),
                edit_section,
                ft.Divider(),
                ft.Row(
                    [ft.Button("Закрити", on_click=lambda e: (
                        page.overlay.remove(focus_view),
                        page.update(),
                        ACTIVE_ELEMENTS.update({"focus_freq_field": None}),
                    ))],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=10,
            expand=True,
        ),
    )

    page.overlay.append(focus_view)
    page.update()
    sync_focus_map_and_repaint()


# ---------- Головне вікно ----------
async def main(page: ft.Page):
    page.title = "C-Helper — Моніторинг частот"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    init_db()
    sync_focus_map_and_repaint()

    status = ft.Text("Status: idle", size=16, color="#90CAF9")
    history = ft.ListView(expand=True, spacing=0, auto_scroll=False)
    global HISTORY_LIST
    HISTORY_LIST = history

    def start_click(e):
        stop_flag.clear()
        threading.Thread(target=fake_poll_loop, daemon=True).start()
        status.value = "✅ Моніторинг запущено"
        page.update()

    def stop_click(e):
        stop_flag.set()
        status.value = "⏹ Зупинено"
        page.update()

    top_row = ft.Row([ft.Button("▶ Start", on_click=start_click),
                      ft.Button("⏹ Stop", on_click=stop_click), status],
                     alignment=ft.MainAxisAlignment.START, spacing=10)

    focus_bar = ft.Row(
        [
            ft.Button("🎯 Робота з фокусом", on_click=lambda e: open_focus_window(page)),
            ft.Button("📋 Дублі", on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Функція у розробці")))),
            ft.Button("📘 Опис частот", on_click=lambda e: page.show_snack_bar(ft.SnackBar(ft.Text("Функція у розробці")))),
            ft.Button("🔄 Оновити описи", on_click=lambda e: (sync_focus_map_and_repaint(),
                                                             page.show_snack_bar(ft.SnackBar(ft.Text("Оновлено (демо)"))))),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        spacing=12,
    )

    page.add(top_row, ft.Divider(), history, ft.Divider(), focus_bar)

    async def refresh_gui():
        """Оновлення моніторингу: нові зверху, без автоскролу, максимум 20 рядків."""
        while True:
            await asyncio.sleep(0.4)
            new_rows = []

            # --- отримуємо всі нові події ---
            try:
                while True:
                    d = event_q.get_nowait()
                    all_events.appendleft(d)
                    new_rows.append(d)
            except Empty:
                pass

            # --- якщо нові є — додаємо їх зверху ---
            if new_rows:
                for ev in reversed(new_rows):  # додаємо у порядку появи
                    focus_col = FOCUS_COLOR_BY_FREQ.get(ev["freq"])

                    row = ft.Container(
                        data={"freq": ev["freq"]},
                        content=ft.Row(
                            [
                                ft.Text(ev["time"], width=58, color="#B0BEC5", size=12),
                                ft.TextButton(
                                    ev["freq"],
                                    on_click=lambda e, f=ev["freq"]: copy_freq_to_clipboard(e, f),
                                    style=ft.ButtonStyle(
                                        color="#4FC3F7",
                                        padding=ft.Padding(0, 0, 0, 0),
                                        bgcolor=None,
                                        overlay_color="rgba(255,255,255,0.05)",
                                    ),
                                ),
                                ft.Text(ev["dur"], width=46, color="#CFD8DC", size=12),
                                ft.Text(ev["src"], width=70, color="#ECEFF1", size=12),
                            ],
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor="#1E1E1E",
                        padding=ft.Padding.symmetric(vertical=2, horizontal=6),
                        border_radius=4,
                        border=ft.Border.all(2, focus_col)
                        if focus_col
                        else ft.Border.all(1, "#444444"),
                        margin=ft.Margin.only(bottom=1),
                    )

                    # ✅ вставляємо нові зверху
                    history.controls.insert(0, row)

                # 🧹 зберігаємо тільки 20 рядків
                if len(history.controls) > 20:
                    del history.controls[20:]

                # 🔄 не скаче скрол, просто оновлюємо
                page.update()

                # 🟡 якщо кольори фокусів змінювались — оновлюємо рамки
                apply_focus_to_history(history)

    asyncio.create_task(refresh_gui())


# ---------- Запуск ----------
if __name__ == "__main__":
    ft.run(main)
