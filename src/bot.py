import logging
import os
from utils.utils import read_textfile, write_textfile
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
from typing import Optional

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

WAITING_FOR_RULES = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.

    Sends a welcome message to the user when they start the bot.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="¡Hola! Soy PatasBot. Estoy aquí para ayudarte con las reglas del grupo, "
        "crear encuestas para invitar a otras personas y más.",
    )


async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the event when a new member joins the group.

    Sends a welcome message to the new member and shows them the rules of the group.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.
    """
    for new_member in update.message.new_chat_members:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"¡Hola {new_member.username or new_member.first_name}! Bienvenide al grupo. ",
        )

    await rules(update, context)


async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /rules command.

    Sends the current rules of the group to the user.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.
    """
    rules_text = read_textfile("rules.txt")
    if not rules_text.strip():
        rules_text = "Aún no se han establecido reglas para este grupo."
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=rules_text
    )


async def change_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the command to change the rules of the bot.

    Checks if the user issuing the command is an admin. If not, sends a permission error message.
    If the user is an admin, prompts them to reply with the new rules or cancel the operation.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.

    Returns:
        int: The next state in the conversation handler, or ConversationHandler.END if not permitted.
    """
    admin_id = get_admin_id()
    if update.effective_user.id != admin_id:
        await update.message.reply_text("No tienes permiso para cambiar las reglas")
        return ConversationHandler.END

    await update.message.reply_text(
        "Responde a este mensaje con las nuevas reglas, o pon /cancel para cancelar"
    )

    return WAITING_FOR_RULES


async def receive_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the new rules from the user and saves them to a text file.

    If the rules are successfully saved, sends a confirmation message.
    If there is an error saving the rules, sends an error message.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.

    Returns:
        int: ConversationHandler.END to indicate the end of the conversation.
    """
    success_write: bool = write_textfile("rules.txt", update.message.text)

    if success_write:
        await update.message.reply_text("Reglas guardadas correctamente")
    else:
        await update.message.reply_text("Ha ocurrido un error guardando las reglas")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels the current operation and ends the conversation.

    Sends a cancellation message to the user.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.

    Returns:
        int: ConversationHandler.END to indicate the end of the conversation.
    """
    await update.message.reply_text("Operación cancelada")

    return ConversationHandler.END


def get_token() -> str:
    """
    Retrieves the bot token from environment variables.

    Raises:
        ValueError: If the TOKEN environment variable is not set.

    Returns:
        str: The bot token.
    """
    token: Optional[str] = os.getenv("TOKEN")
    if not token:
        logging.error("No TOKEN found in environment variables.")
        raise ValueError("TOKEN is required but not set in environment variables.")
    return token


def get_admin_id() -> int:
    """
    Retrieves the admin ID from environment variables.

    Raises:
        ValueError: If the ADMIN_ID environment variable is not set.

    Returns:
        int: The admin ID.
    """
    admin_id: Optional[str] = os.getenv("ADMIN_ID")
    if not admin_id:
        logging.error("No ADMIN_ID found in environment variables.")
        raise ValueError("ADMIN_ID is required but not set in environment variables.")
    return int(admin_id)


if __name__ == "__main__":
    application = ApplicationBuilder().token(get_token()).build()

    start_handler = CommandHandler("start", start)
    new_member_handler = MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member
    )
    rules_handler = CommandHandler("rules", rules)

    change_rules_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("change_rules", change_rules)],
        states={
            WAITING_FOR_RULES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_rules)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )

    application.add_handler(start_handler)
    application.add_handler(new_member_handler)
    application.add_handler(rules_handler)
    application.add_handler(change_rules_conv_handler)

    application.run_polling()
