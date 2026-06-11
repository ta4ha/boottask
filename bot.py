import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

PRIORITY = {
    "!1": ("🔴 عاجل", 1),
    "!2": ("🟡 مهم", 2),
    "!3": ("🟢 عادي", 3),
}

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def parse_message(text):
    priority_label = "🟢 عادي"
    priority_num = 3
    due_date = None

    for code, (label, num) in PRIORITY.items():
        if code in text:
            priority_label = label
            priority_num = num
            text = text.replace(code, "").strip()

    if "@" in text:
        parts = text.split("@")
        text = parts[0].strip()
        due_date = parts[1].strip()

    return text, priority_label, priority_num, due_date

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    raw = update.message.text.strip()
    text, priority_label, priority_num, due_date = parse_message(raw)
    tasks = load_tasks()
    if user_id not in tasks:
        tasks[user_id] = []
    task = {"text": text, "done": False, "priority": priority_label, "priority_num": priority_num, "due": due_date}
    tasks[user_id].append(task)
    save_tasks(tasks)
    num = len(tasks[user_id])
    due_str = f"\n📅 الاستحقاق: {due_date}" if due_date else ""
    await update.message.reply_text(f"✅ تمت إضافة المهمة رقم {num}:\n📌 {text}\n{priority_label}{due_str}")

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    user_tasks = tasks.get(user_id, [])
    if not user_tasks:
        await update.message.reply_text("📭 لا توجد مهام حالياً.")
        return
    sorted_tasks = sorted(enumerate(user_tasks), key=lambda x: (x[1].get("priority_num", 3), x[1]["done"]))
    msg = "📋 *قائمة مهامك:*\n\n"
    for orig_i, task in sorted_tasks:
        status = "✅" if task["done"] else "🔲"
        due_str = f" | 📅 {task['due']}" if task.get("due") else ""
        msg += f"{status} {orig_i+1}. {task['text']} | {task.get('priority','🟢 عادي')}{due_str}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    user_tasks = tasks.get(user_id, [])
    try:
        num = int(context.args[0]) - 1
        if num < 0 or num >= len(user_tasks):
            raise ValueError
        user_tasks[num]["done"] = True
        save_tasks(tasks)
        await update.message.reply_text(f"✅ تم إنجاز المهمة: {user_tasks[num]['text']}")
    except:
        await update.message.reply_text("⚠️ مثال: /done 1")

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    user_tasks = tasks.get(user_id, [])
    try:
        num = int(context.args[0]) - 1
        if num < 0 or num >= len(user_tasks):
            raise ValueError
        removed = user_tasks.pop(num)
        save_tasks(tasks)
        await update.message.reply_text(f"🗑️ تم حذف المهمة: {removed['text']}")
    except:
        await update.message.reply_text("⚠️ مثال: /delete 1")

async def clear_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    user_tasks = tasks.get(user_id, [])
    tasks[user_id] = [t for t in user_tasks if not t["done"]]
    save_tasks(tasks)
    await update.message.reply_text("🧹 تم مسح جميع المهام المنجزة.")

async def morning_reminder(context: ContextTypes.DEFAULT_TYPE):
    tasks = load_tasks()
    for user_id, user_tasks in tasks.items():
        pending = [t for t in user_tasks if not t["done"]]
        if not pending:
            continue
        msg = "☀️ *صباح الخير! مهامك لهذا اليوم:*\n\n"
        sorted_tasks = sorted(pending, key=lambda x: x.get("priority_num", 3))
        for i, task in enumerate(sorted_tasks, 1):
            due_str = f" | 📅 {task['due']}" if task.get("due") else ""
            msg += f"🔲 {i}. {task['text']} | {task.get('priority','🟢 عادي')}{due_str}\n"
        try:
            await context.bot.send_message(chat_id=int(user_id), text=msg, parse_mode="Markdown")
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً! أنا بوت المهام الخاص بك.\n\n"
        "📌 أرسل أي رسالة لإضافتها كمهمة\n\n"
        "*الأولوية:*\n"
        "أضف !1 للعاجل 🔴\n"
        "أضف !2 للمهم 🟡\n"
        "أضف !3 للعادي 🟢\n\n"
        "*تاريخ الاستحقاق:*\n"
        "أضف @15/6 لتحديد التاريخ 📅\n\n"
        "*مثال:* مراجعة التقرير !1 @15/6\n\n"
        "/tasks — عرض المهام\n"
        "/done 1 — إنجاز مهمة\n"
        "/delete 1 — حذف مهمة\n"
        "/clear — مسح المنجزة\n\n"
        "☀️ ستصلك تذكير صباحي يومياً بمهامك"
    )

TOKEN = "8992646379:AAHTEfs4QJdxYLTen1ZGGn9vF85XbnsJQTw"

app = ApplicationBuilder().token(TOKEN).build()

app.job_queue.run_daily(morning_reminder, time=datetime.strptime("08:00", "%H:%M").time())

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tasks", show_tasks))
app.add_handler(CommandHandler("done", done_task))
app.add_handler(CommandHandler("delete", delete_task))
app.add_handler(CommandHandler("clear", clear_done))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_task))

print("🤖 البوت يعمل...")
app.run_polling()
