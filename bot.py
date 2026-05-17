import telebot
import schedule
import threading
import time
import json
import os
import re
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

TASKS_FILE = "tasks.json"
CHAT_ID = None


def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []

    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except:
            return []


def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)


def add_tasks(task_texts):
    tasks = load_tasks()

    for t in task_texts:
        clean = t.strip()
        if clean:
            tasks.append({
                "text": clean,
                "done": False
            })

    save_tasks(tasks)


def normalize_tasks_text(text):
    text = text.replace("،", "\n")
    text = text.replace(",", "\n")
    text = text.replace(" و ", "\n")
    text = text.replace(" و", "\n")
    text = text.replace("و ", "\n")

    parts = [p.strip() for p in text.split("\n") if p.strip()]
    return parts


def normalize(s):
    s = s.lower().strip()
    s = re.sub(r"[^\w\u0600-\u06FF\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


@bot.message_handler(commands=["start"])
def start(message):
    global CHAT_ID
    CHAT_ID = message.chat.id

    bot.send_message(
        CHAT_ID,
        "🚀 البوت شغال\n\n"
        "ابعت التاسكات بتاعتك كـ text.\n"
        "مثال:\n\n"
        "اذاكر flutter\n"
        "اخلص المشروع\n"
        "انزل الجيم\n\n"
        "ولو خلصت حاجة ابعت:\n"
        "done اسم التاسك"
    )


@bot.message_handler(commands=["tasks"])
def show_tasks(message):
    tasks = load_tasks()

    if not tasks:
        bot.send_message(message.chat.id, "مفيش تاسكات حاليا.")
        return

    msg = "📋 التاسكات:\n\n"
    for i, task in enumerate(tasks, start=1):
        status = "✅" if task.get("done") else "⏳"
        msg += f"{i}. {status} {task.get('text')}\n"

    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=["clear"])
def clear_done_tasks(message):
    tasks = load_tasks()
    tasks = [t for t in tasks if not t.get("done", False)]
    save_tasks(tasks)
    bot.reply_to(message, "🧹 تم حذف التاسكات المكتملة")


@bot.message_handler(func=lambda m: m.text is not None)
def handle_text(message):
    global CHAT_ID
    CHAT_ID = message.chat.id

    text = message.text.strip()

    if text.startswith("/"):
        return

    low = text.lower()

    done_words = ["done", "خلصت", "عملت", "انهيت", "خلص", "خلصت"]
    is_done_message = any(word in low for word in done_words)

    tasks = load_tasks()

    if is_done_message:
        found_tasks = []

        norm_message = normalize(text)

        for task in tasks:
            if task.get("done", False):
                continue

            task_text = task.get("text", "")
            norm_task = normalize(task_text)

            if norm_task and norm_task in norm_message:
                task["done"] = True
                found_tasks.append(task_text)
                continue

            task_words = [w for w in norm_task.split() if len(w) > 2]
            if task_words and all(w in norm_message for w in task_words[:2]):
                task["done"] = True
                found_tasks.append(task_text)

        save_tasks(tasks)

        if found_tasks:
            msg = "✅ تمام خلصت:\n\n"
            for t in found_tasks:
                msg += f"- {t}\n"
            bot.reply_to(message, msg)
        else:
            bot.reply_to(message, "❌ مفهمتش انهي تاسك خلصته. ابعت:\n done اسم التاسك")
        return

    new_tasks = normalize_tasks_text(text)
    add_tasks(new_tasks)

    response = "✅ تمت إضافة التاسكات:\n\n"
    for task in new_tasks:
        response += f"- {task}\n"

    bot.reply_to(message, response)


def remind_tasks():
    if CHAT_ID is None:
        return

    tasks = load_tasks()
    pending = [t for t in tasks if not t.get("done", False)]

    if not pending:
        return

    msg = "⏰ التاسكات اللي عليك:\n\n"
    for i, task in enumerate(pending, start=1):
        msg += f"{i}. {task.get('text')}\n"

    bot.send_message(CHAT_ID, msg)


def ask_daily_tasks():
    if CHAT_ID is None:
        return

    bot.send_message(
        CHAT_ID,
        "🎯 ابعت التاسكات الجديدة بتاعت النهارده"
    )


schedule.every(1).hours.do(remind_tasks)
schedule.every().day.at("12:00").do(ask_daily_tasks)


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


threading.Thread(target=run_scheduler, daemon=True).start()

print("🚀 BOT RUNNING...")
bot.infinity_polling()