import customtkinter as ctk
import sqlite3
from datetime import date, datetime
from tkinter import messagebox
import matplotlib.pyplot as plt

# === Налаштування вікна ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Фітнес-трекер прогресу")
app.geometry("700x700")

# === Створюємо базу даних ===
conn = sqlite3.connect('gym_progress.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise TEXT,
            date TEXT,
            sets INTEGER,
            reps TEXT
            )''')
conn.commit()

# === Оновлення списку вправ ===
def update_exercise_list(selected_exercise=None):
    c.execute("SELECT DISTINCT exercise FROM workouts")
    exercises = [row[0] for row in c.fetchall()]
    exercise_dropdown.configure(values=exercises)
    if selected_exercise:
        exercise_dropdown.set(selected_exercise)
    elif exercises:
        exercise_dropdown.set(exercises[0])

# === Функція для збереження даних ===
def save_workout():
    exercise = entry_exercise.get().strip()
    workout_date_str = entry_date.get().strip()
    sets = entry_sets.get().strip()
    reps = entry_reps.get().strip()

    if not (exercise and workout_date_str and sets and reps):
        messagebox.showerror("Помилка", "Будь ласка, заповни всі поля!")
        return

    try:
        # Форматуємо дату у формат YYYY-MM-DD
        workout_date = datetime.strptime(workout_date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        sets = int(sets)

        c.execute("INSERT INTO workouts (exercise, date, sets, reps) VALUES (?, ?, ?, ?)",
                  (exercise, workout_date, sets, reps))
        conn.commit()

        messagebox.showinfo("Успіх", f"Тренування для '{exercise}' збережено!")
        entry_exercise.delete(0, 'end')
        entry_sets.delete(0, 'end')
        entry_reps.delete(0, 'end')
        entry_date.delete(0, 'end')
        entry_date.insert(0, str(date.today()))

        # Оновити список вправ і вибрати нову
        update_exercise_list(selected_exercise=exercise)

    except ValueError:
        messagebox.showerror("Помилка", "Перевір правильність введених даних!")

# === Побудова графіка динаміки (стовпчиковий із візуальним поділом по датах) ===
def show_progress():
    import re

    exercise = exercise_dropdown.get()
    start_date = entry_start_date.get()
    end_date = entry_end_date.get()

    if not exercise:
        messagebox.showerror("Помилка", "Оберіть назву вправи для аналізу!")
        return

    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        messagebox.showerror("Помилка", "Невірний формат дати! Використовуй YYYY-MM-DD.")
        return

    # Використовуємо SQLite date() для коректного порівняння дат
    c.execute("""
        SELECT date, reps 
        FROM workouts 
        WHERE exercise = ? 
          AND date(date) BETWEEN date(?) AND date(?) 
        ORDER BY date(date)
    """, (exercise, start_date, end_date))
    data = c.fetchall()

    if not data:
        messagebox.showinfo("Немає даних", "За цей період даних не знайдено.")
        return

    all_reps = []
    all_dates = []

    for d, reps_str in data:
        reps_list = [int(x) for x in re.split(r'[ ,;]+', reps_str) if x.strip().isdigit()]
        for i, rep in enumerate(reps_list, start=1):
            all_reps.append(rep)
            all_dates.append(f"{d} (Підхід {i})")

    plt.figure(figsize=(10, 5))

    # Виділення кожної дати напівпрозорим фоном
    unique_dates = sorted(set(d.split(' ')[0] for d in all_dates))
    for ud in unique_dates:
        positions = [i for i, x in enumerate(all_dates) if x.startswith(ud)]
        if positions:
            plt.axvspan(positions[0] - 0.5, positions[-1] + 0.5, color='lightgray', alpha=0.2)

    plt.bar(all_dates, all_reps, color='deepskyblue', edgecolor='black')
    plt.title(f"Динаміка повторень: {exercise}")
    plt.xlabel("Дата і підхід")
    plt.ylabel("Кількість повторень")
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

# === Перевірка вмісту бази (debug) ===
def show_all_data():
    c.execute("SELECT * FROM workouts")
    rows = c.fetchall()
    if not rows:
        print("\n[База порожня]\n")
    else:
        print("\n=== Вміст бази даних ===")
        for r in rows:
            print(r)
        print("========================\n")

# === Інтерфейс ===
label_title = ctk.CTkLabel(app, text="Додати тренування", font=("Arial", 20, "bold"))
label_title.pack(pady=10)

entry_exercise = ctk.CTkEntry(app, placeholder_text="Назва вправи")
entry_exercise.pack(pady=10)

entry_date = ctk.CTkEntry(app)
entry_date.insert(0, str(date.today()))
entry_date.pack(pady=10)

entry_sets = ctk.CTkEntry(app, placeholder_text="Кількість підходів")
entry_sets.pack(pady=10)

entry_reps = ctk.CTkEntry(app, placeholder_text="Повторення у кожному підході (наприклад 12,10,8)")
entry_reps.pack(pady=10)

btn_save = ctk.CTkButton(app, text="Зберегти тренування", command=save_workout)
btn_save.pack(pady=10)

# === Секція аналізу ===
label_analyze = ctk.CTkLabel(app, text="Перегляд динаміки", font=("Arial", 18, "bold"))
label_analyze.pack(pady=15)

exercise_dropdown = ctk.CTkOptionMenu(app, values=[""], width=250)
exercise_dropdown.pack(pady=5)

entry_start_date = ctk.CTkEntry(app, placeholder_text="Початкова дата (YYYY-MM-DD)")
entry_start_date.pack(pady=5)

entry_end_date = ctk.CTkEntry(app, placeholder_text="Кінцева дата (YYYY-MM-DD)")
entry_end_date.pack(pady=5)

btn_show = ctk.CTkButton(app, text="Показати динаміку", command=show_progress)
btn_show.pack(pady=10)

# === Кнопка для перевірки бази ===
btn_debug = ctk.CTkButton(app, text="🧠 Перевірити дані (консоль)", command=show_all_data)
btn_debug.pack(pady=10)

update_exercise_list()
app.mainloop()
