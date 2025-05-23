import logging
import os
from utils.utils import read_textfile
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bot initialized"
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=read_textfile("rules.txt")
    )


if __name__ == "__main__":
    token = os.getenv("TOKEN")
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler("start", start)
    rules_handler = CommandHandler("rules", rules)

    application.add_handler(start_handler)
    application.add_handler(rules_handler)

    application.run_polling()
