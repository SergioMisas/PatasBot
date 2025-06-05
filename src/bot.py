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

# Conversation states
WAITING_FOR_RULES = 1

# Constants
POLL_DURATION = 86400  # Default: 86400, 24 hours in seconds


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)


"""
Start
"""


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
        "crear encuestas para invitar a otras personas y más. Escribe /patas_help "
        "para ver los comandos disponibles.",
    )


"""
New Member
"""


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


"""
Rules
"""


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
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rules_text)


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
        await update.message.reply_text("No tienes permiso para cambiar las reglas.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Responde a este mensaje con las nuevas reglas, o pon /cancel para cancelar."
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
        await update.message.reply_text("Reglas guardadas correctamente.")
    else:
        await update.message.reply_text("Ha ocurrido un error guardando las reglas.")

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
    await update.message.reply_text("Operación cancelada.")

    return ConversationHandler.END


"""
Invite Poll
"""


async def create_invite_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Creates a poll to invite a user to the group.
    The user to be invited must be mentioned with an @username.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.
    """
    if not await has_privileges_for_invite(update, context):
        return

    if len(context.args) != 1 or not context.args[0].startswith("@"):
        await update.message.reply_text(
            "Usuario no válido. Por favor, menciona a un usuario con @."
        )
        return

    username = context.args[0]
    question = f"Meter a {username}"
    options = ["Sí", "No sé si sí", "No sé si no", "No"]

    poll = await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=options,
        is_anonymous=True,
        allows_multiple_answers=False,
    )

    await context.bot.pin_chat_message(
        chat_id=update.effective_chat.id,
        message_id=poll.message_id,
    )

    context.job_queue.run_once(
        callback=close_poll_callback,
        when=POLL_DURATION,
        data={
            "chat_id": update.effective_chat.id,
            "message_id": poll.message_id,
            "username": username,
            "requested_by": update.effective_user.id,
        },
        name=f"close_poll_{update.effective_chat.id}_{username}",
    )


async def has_privileges_for_invite(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """
    Checks if the bot has privileges to create an invite poll in the current group.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.

    Returns:
        bool: True if the bot has the necessary privileges, False otherwise.
    """
    bot_member = await context.bot.get_chat_member(
        chat_id=update.effective_chat.id, user_id=context.bot.id
    )

    if (
        bot_member.status != "administrator"
        or not getattr(bot_member, "can_pin_messages", False)
        or not getattr(bot_member, "can_invite_users", False)
    ):
        await update.message.reply_text(
            "No tengo permisos para crear encuestas de invitación en este grupo. "
            "Asegúrate de que soy administrador y tengo los permisos necesarios:\n"
            "- Fijar mensajes\n"
            "- Invitar usuarios"
        )
        return False

    return True


async def close_poll_callback(context: ContextTypes.DEFAULT_TYPE):
    """
    Callback function to close the poll after 24 hours.
    Retrieves the poll data from the job context and stops the poll.

    It also decides whether to invite the user based on the poll results (WIP).

    Args:
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.
    """
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    username = job_data["username"]

    stopped_poll = await context.bot.stop_poll(
        chat_id=chat_id,
        message_id=message_id,
    )

    await context.bot.unpin_chat_message(
        chat_id=chat_id,
        message_id=message_id,
    )

    results = [(option.text, option.voter_count) for option in stopped_poll.options]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Resultados de la encuesta para invitar a {username}:\n"
        + "\n".join([f"{text}: {count}" for text, count in results]),
    )


async def cancel_invite_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels the invite poll for a username if it is still active.

    Args:
        update (Update): The incoming update from Telegram.
        context (ContextTypes.DEFAULT_TYPE): The context for the callback.
    """
    if len(context.args) != 1 or not context.args[0].startswith("@"):
        await update.message.reply_text(
            "Usuario no válido. Por favor, menciona a un usuario con @."
        )
        return

    username = context.args[0]
    job_name = f"close_poll_{update.effective_chat.id}_{username}"

    jobs = context.job_queue.get_jobs_by_name(job_name)
    if not jobs:
        await update.message.reply_text(
            f"No hay una encuesta activa para invitar a {username}."
        )
        return

    for job in jobs:
        if job.data["requested_by"] != update.effective_user.id:
            await update.message.reply_text(
                "Solo el usuario que creó la encuesta puede cancelarla."
            )
            return
        await context.bot.unpin_chat_message(
            chat_id=update.effective_chat.id,
            message_id=job.data["message_id"],
        )
        job.schedule_removal()

    await update.message.reply_text(f"Encuesta para invitar a {username} cancelada.")


"""
Utility Functions
"""


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


"""
Main Function
"""


def register_handlers(application: ApplicationBuilder):
    """
    Registers the command and message handlers for the bot.

    Args:
        application (ApplicationBuilder): The application instance to register handlers with.
    """
    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(
        CommandHandler(
            "invite",
            create_invite_poll,
            filters=filters.ChatType.GROUP | filters.ChatType.SUPERGROUP,
        )
    )
    application.add_handler(
        CommandHandler(
            "cancelinvite",
            cancel_invite_poll,
            filters=filters.ChatType.GROUP | filters.ChatType.SUPERGROUP,
        )
    )

    # Message Handlers
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member)
    )

    # Conversation Handlers
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("changerules", change_rules)],
            states={
                WAITING_FOR_RULES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_rules)
                ]
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            per_user=True,
        )
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(get_token()).build()
    register_handlers(application)

    application.run_polling()
