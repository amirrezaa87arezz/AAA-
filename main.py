import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

with open("arvox_knowledge.json", "r", encoding="utf-8") as f:
    KNOWLEDGE = json.load(f)

flat_knowledge = {}
for category in KNOWLEDGE.values():
    flat_knowledge.update(category)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🤖 *دستیار و هوش مصنوعی آروکس* خوش‌اومدی!

Arvox یک ربات هوشمند بدون نیاز به اینترنت خارجی، پاسخگوی سوالات توست.
- پشتیبانی از زبان فارسی
- پاسخ از دیتابیس دانش داخلی
- بدون محدودیت و خطا

✨ *برنامه دستیار هوشمند آروکس به‌زودی منتشر خواهد شد...*
    """
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text.strip()
    response = flat_knowledge.get(user_msg, "متاسفم قربان، هنوز جواب این سوال رو توی بانک اطلاعاتیم ندارم.")
    await update.message.reply_text(response)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()