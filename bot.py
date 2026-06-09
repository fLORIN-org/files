import telebot
from telebot import types
import sqlite3
from datetime import datetime
import threading
import time
from flask import Flask
from os import environ

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 8080)))

TOKEN = "8984243496:AAGYq5NsReMk5wwpLrB_tfkVYBQU4W-XRyI"

bot = telebot.TeleBot(TOKEN)

GROUPS = ["9/2-РПО-25/1", "9/2-РПО-25/2"]

DAYS = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
}

TIMES = {
    1: "8:00–9:30",
    2: "9:45–11:15",
    3: "11:30–13:00",
    4: "13:15–14:45",
    5: "15:00–16:30",
}


def db():
    return sqlite3.connect("college.db")


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            name TEXT,
            group_name TEXT,
            registered_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            day_of_week INTEGER,
            lesson_number INTEGER,
            subject TEXT,
            teacher TEXT,
            room TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            description TEXT,
            due_date TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            sent_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = c.fetchone()
    conn.close()
    return user


def save_user(telegram_id, name, group_name):
    conn = db()
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        INSERT INTO users (telegram_id, name, group_name, registered_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            name = excluded.name,
            group_name = excluded.group_name
    """, (telegram_id, name, group_name, now))
    conn.commit()
    conn.close()


def get_schedule(group_name, day):
    conn = db()
    c = conn.cursor()
    c.execute("""
        SELECT lesson_number, subject, teacher, room
        FROM schedule
        WHERE group_name = ? AND day_of_week = ?
        ORDER BY lesson_number
    """, (group_name, day))
    rows = c.fetchall()
    conn.close()
    return rows


def get_lesson(group_name, day, num):
    conn = db()
    c = conn.cursor()
    c.execute("""
        SELECT lesson_number, subject, teacher, room
        FROM schedule
        WHERE group_name = ? AND day_of_week = ? AND lesson_number = ?
    """, (group_name, day, num))
    row = c.fetchone()
    conn.close()
    return row


def get_homework(subject):
    conn = db()
    c = conn.cursor()
    c.execute("""
        SELECT description, due_date FROM homework
        WHERE subject = ?
        ORDER BY due_date DESC LIMIT 1
    """, (subject,))
    row = c.fetchone()
    conn.close()
    return row


def get_all_users():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def fill_test_data():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM schedule")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    schedule = [
        # 9/2-РПО-25/1
        ("9/2-РПО-25/1", 0, 1, "Русский язык", "Петрова А.В.", "Цоколь 1"),
        ("9/2-РПО-25/1", 0, 2, "Математика", "Иванов С.П.", "Аудитория 3"),
        ("9/2-РПО-25/1", 0, 3, "Введение в специальность", "Козлов Д.А.", "Аудитория 7"),

        ("9/2-РПО-25/1", 1, 1, "Литература", "Смирнова Е.И.", "Аудитория 1"),
        ("9/2-РПО-25/1", 1, 2, "Физика", "Новиков В.С.", "Цоколь 2"),
        ("9/2-РПО-25/1", 1, 3, "Введение в Python", "Морозов И.К.", "Аудитория 5"),
        ("9/2-РПО-25/1", 1, 4, "Введение в Python", "Морозов И.К.", "Аудитория 5"),

        ("9/2-РПО-25/1", 2, 1, "Математика", "Иванов С.П.", "Аудитория 3"),
        ("9/2-РПО-25/1", 2, 2, "Иностранный язык", "Сидорова Н.И.", "Аудитория 2"),
        ("9/2-РПО-25/1", 2, 3, "Основы ИТ", "Козлов Д.А.", "Аудитория 6"),
        ("9/2-РПО-25/1", 2, 4, "Основы ИТ", "Козлов Д.А.", "Аудитория 6"),

        ("9/2-РПО-25/1", 3, 1, "История", "Волкова Е.М.", "Аудитория 4"),
        ("9/2-РПО-25/1", 3, 2, "Физика", "Новиков В.С.", "Цоколь 2"),
        ("9/2-РПО-25/1", 3, 3, "Конфигурирование Windows", "Зайцев П.Р.", "Аудитория 8"),

        ("9/2-РПО-25/1", 4, 1, "Физическая культура", "Лебедев А.С.", "Цоколь 3"),
        ("9/2-РПО-25/1", 4, 2, "ОБЖ", "Соколов М.В.", "Аудитория 9"),
        ("9/2-РПО-25/1", 4, 3, "Введение в Python", "Морозов И.К.", "Аудитория 5"),

        # 9/2-РПО-25/2
        ("9/2-РПО-25/2", 0, 1, "Математика", "Иванов С.П.", "Аудитория 3"),
        ("9/2-РПО-25/2", 0, 2, "Русский язык", "Петрова А.В.", "Аудитория 1"),
        ("9/2-РПО-25/2", 0, 3, "Введение в Python", "Морозов И.К.", "Аудитория 5"),
        ("9/2-РПО-25/2", 0, 4, "Введение в Python", "Морозов И.К.", "Аудитория 5"),

        ("9/2-РПО-25/2", 1, 1, "Физика", "Новиков В.С.", "Цоколь 2"),
        ("9/2-РПО-25/2", 1, 2, "Литература", "Смирнова Е.И.", "Аудитория 2"),
        ("9/2-РПО-25/2", 1, 3, "Основы ИТ", "Козлов Д.А.", "Аудитория 6"),

        ("9/2-РПО-25/2", 2, 1, "Иностранный язык", "Сидорова Н.И.", "Аудитория 2"),
        ("9/2-РПО-25/2", 2, 2, "Математика", "Иванов С.П.", "Аудитория 3"),
        ("9/2-РПО-25/2", 2, 3, "Конфигурирование Windows", "Зайцев П.Р.", "Аудитория 8"),
        ("9/2-РПО-25/2", 2, 4, "Конфигурирование Windows", "Зайцев П.Р.", "Аудитория 8"),

        ("9/2-РПО-25/2", 3, 1, "Физика", "Новиков В.С.", "Цоколь 2"),
        ("9/2-РПО-25/2", 3, 2, "История", "Волкова Е.М.", "Аудитория 4"),
        ("9/2-РПО-25/2", 3, 3, "Введение в специальность", "Козлов Д.А.", "Аудитория 7"),

        ("9/2-РПО-25/2", 4, 1, "Физическая культура", "Лебедев А.С.", "Цоколь 3"),
        ("9/2-РПО-25/2", 4, 2, "Введение в Python", "Морозов И.К.", "Аудитория 5"),
        ("9/2-РПО-25/2", 4, 3, "ОБЖ", "Соколов М.В.", "Аудитория 10"),
    ]

    c.executemany("""
        INSERT INTO schedule (group_name, day_of_week, lesson_number, subject, teacher, room)
        VALUES (?, ?, ?, ?, ?, ?)
    """, schedule)

    homework = [
        ("Математика", "Задачи 5.1–5.10 стр. 87", "2025-06-15"),
        ("Введение в Python", "Написать программу с циклом for", "2025-06-16"),
        ("Русский язык", "Упр. 142, 143", "2025-06-14"),
        ("Физика", "Параграф 12, вопросы 1–5", "2025-06-17"),
        ("Иностранный язык", "Прочитать текст стр. 56, перевод", "2025-06-13"),
        ("Основы ИТ", "Конспект по теме 'Виды ПО'", "2025-06-18"),
        ("Конфигурирование Windows", "Практическая работа №3", "2025-06-19"),
    ]

    c.executemany("""
        INSERT INTO homework (subject, description, due_date)
        VALUES (?, ?, ?)
    """, homework)

    conn.commit()
    conn.close()
    print("Тестовые данные добавлены")


def format_day(lessons, day_name):
    if not lessons:
        return f"*{day_name}*\n\nПар нет"

    text = f"*{day_name}*\n\n"
    for num, subject, teacher, room in lessons:
        t = TIMES.get(num, "—")
        text += f"{num} пара · {t}\n{subject}\n{teacher} · ауд. {room}\n\n"
    return text.strip()


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Расписание на сегодня", "Расписание на неделю")
    kb.row("Профиль", "Сменить группу")
    return kb


def is_registered(message):
    user = get_user(message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Сначала выбери группу — напиши /start")
        return False
    return True


@bot.message_handler(commands=["start"])
def cmd_start(message):
    kb = types.InlineKeyboardMarkup()
    for g in GROUPS:
        kb.add(types.InlineKeyboardButton(g, callback_data=f"group_{g}"))

    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\n\nВыбери свою группу:",
        reply_markup=kb
    )


@bot.message_handler(func=lambda m: m.text == "Расписание на сегодня")
def btn_today(message):
    if not is_registered(message):
        return

    user = get_user(message.from_user.id)
    group = user[3]
    today = datetime.now().weekday()

    if today >= 5:
        bot.send_message(message.chat.id, "Сегодня выходной")
        return

    lessons = get_schedule(group, today)
    text = format_day(lessons, DAYS[today])

    kb = types.InlineKeyboardMarkup(row_width=3)
    if lessons:
        kb.add(*[
            types.InlineKeyboardButton(f"{n} пара", callback_data=f"lesson_{today}_{n}")
            for n, *_ in lessons
        ])

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "Расписание на неделю")
def btn_week(message):
    if not is_registered(message):
        return

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(*[
        types.InlineKeyboardButton(name, callback_data=f"day_{num}")
        for num, name in DAYS.items()
    ])

    bot.send_message(message.chat.id, "Выбери день:", reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "Профиль")
def btn_profile(message):
    user = get_user(message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Сначала выбери группу — напиши /start")
        return

    _, tid, name, group, reg_at = user
    bot.send_message(
        message.chat.id,
        f"*{name}*\nГруппа: {group}\nВ боте с: {reg_at[:10]}",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "Сменить группу")
def btn_change_group(message):
    kb = types.InlineKeyboardMarkup()
    for g in GROUPS:
        kb.add(types.InlineKeyboardButton(g, callback_data=f"group_{g}"))
    bot.send_message(message.chat.id, "Выбери группу:", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("group_"))
def cb_group(call):
    group = call.data.replace("group_", "")
    save_user(call.from_user.id, call.from_user.first_name, group)
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"Группа {group} сохранена",
        reply_markup=main_menu()
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("day_"))
def cb_day(call):
    day = int(call.data.replace("day_", ""))
    user = get_user(call.from_user.id)
    group = user[3]

    lessons = get_schedule(group, day)
    text = format_day(lessons, DAYS[day])

    kb = types.InlineKeyboardMarkup(row_width=3)
    if lessons:
        kb.add(*[
            types.InlineKeyboardButton(f"{n} пара", callback_data=f"lesson_{day}_{n}")
            for n, *_ in lessons
        ])
    kb.add(types.InlineKeyboardButton("← Назад", callback_data="back_days"))

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("lesson_"))
def cb_lesson(call):
    _, day, num = call.data.split("_")
    day, num = int(day), int(num)

    user = get_user(call.from_user.id)
    group = user[3]
    lesson = get_lesson(group, day, num)

    if not lesson:
        bot.answer_callback_query(call.id, "Пара не найдена")
        return

    n, subject, teacher, room = lesson
    hw = get_homework(subject)

    text = f"*{subject}*\n\n"
    text += f"{num} пара · {TIMES.get(num, '—')}\n"
    text += f"Преподаватель: {teacher}\n"
    text += f"Аудитория: {room}\n\n"

    if hw:
        desc, due = hw
        text += f"*Домашнее задание:*\n{desc}\nСдать до {due}"
    else:
        text += "Домашнего задания нет"

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("← Назад", callback_data=f"day_{day}"))

    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "back_days")
def cb_back_days(call):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(*[
        types.InlineKeyboardButton(name, callback_data=f"day_{num}")
        for num, name in DAYS.items()
    ])
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "Выбери день:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb
    )


def notification_loop():
    while True:
        now = datetime.now()
        if now.hour == 20 and now.minute == 0:
            tomorrow = now.weekday() + 1
            if tomorrow in DAYS:
                for tid in get_all_users():
                    user = get_user(tid)
                    if not user:
                        continue
                    group = user[3]
                    lessons = get_schedule(group, tomorrow)
                    text = f"Завтра {DAYS[tomorrow]}:\n\n" + format_day(lessons, DAYS[tomorrow])
                    try:
                        bot.send_message(tid, text, parse_mode="Markdown")
                    except Exception as e:
                        print(f"Не удалось отправить {tid}: {e}")

                conn = db()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO notifications (text, sent_at) VALUES (?, ?)",
                    (f"Рассылка на {DAYS[tomorrow]}", now.strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()

        time.sleep(60)


if __name__ == "__main__":
    init_db()
    fill_test_data()
    threading.Thread(target=notification_loop, daemon=True).start()
    threading.Thread(target=run_flask, daemon=True).start()
    print("Бот запущен")
    bot.infinity_polling()
