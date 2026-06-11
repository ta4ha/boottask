import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TASKS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.json")

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return {}
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    tasks = load_tasks()
    if user_id not in tasks:
        tasks[user_id] = []
    tasks[user_id].append({"text": text, "done": False})
    save_tasks(tasks)
    num = len(tasks[user_id])
    await update.message.reply_text(f"✅ تمت إضافة المهمة رقم {num}:\n📌 {text}")

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    user_tasks = tasks.get(user_id, [])
    if not user_tasks:
        await update.message.reply_text("📭 لا توجد مهام حالياً.")
        return
    msg = "📋 *قائمة مهامك:*\n\n"
    for i, task in enumerate(user_tasks, 1):
        status = "✅" if task["done"] else "🔲"
        msg += f"{status} {i}. {task['text']}\n"
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
        await update.message.reply_text("⚠️ اكتب رقم المهمة بشكل صحيح. مثال: /done 1")

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
        await update.message.reply_text("⚠️ اكتب رقم المهمة بشكل صحيح. مثال: /delete 1")

async def clear_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    tasks = load_tasks()
    user_tasks = tasks.get(user_id, [])
    tasks[user_id] = [t for t in user_tasks if not t["done"]]
    save_tasks(tasks)
    await update.message.reply_text("🧹 تم مسح جميع المهام المنجزة.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً! أنا بوت المهام الخاص بك.\n\n"
        "📌 أرسل أي رسالة لإضافتها كمهمة\n"
        "/tasks — عرض المهام\n"
        "/done 1 — إنجاز مهمة\n"
        "/delete 1 — حذف مهمة\n"
        "/clear — مسح المنجزة"
    )

TOKEN = "8992646379:AAHTEfs4QJdxYLTen1ZGGn9vF85XbnsJQTw"

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("tasks", show_tasks))
app.add_handler(CommandHandler("done", done_task))
app.add_handler(CommandHandler("delete", delete_task))
app.add_handler(CommandHandler("clear", clear_done))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_task))

print("🤖 البوت يعمل...")
app.run_polling()
