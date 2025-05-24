import logging
import os
from utils.utils import *
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

WAITING_FOR_RULES = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Bot initialized"
    )


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=read_textfile("rules.txt")
    )


async def change_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Responde a este mensaje con las nuevas reglas, o pon /cancel para cancelar"
    )

    return WAITING_FOR_RULES


async def receive_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    success_write: bool = write_textfile("rules.txt", update.message.text)

    if success_write:
        await update.message.reply_text("Reglas guardadas correctamente")
    else:
        await update.message.reply_text("Ha ocurrido un error guardando las reglas")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada")

    return ConversationHandler.END


if __name__ == "__main__":
    token = os.getenv("TOKEN")
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler("start", start)
    rules_handler = CommandHandler("rules", rules)

    change_rules_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("change_rules", change_rules)],
        states={
            WAITING_FOR_RULES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_rules)
            ]
        },
        fallbacks={CommandHandler("cancel", cancel)},
        per_user=True,
    )

    application.add_handler(start_handler)
    application.add_handler(rules_handler)
    application.add_handler(change_rules_conv_handler)

    application.run_polling()
