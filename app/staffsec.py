"""Telegram Bot to manage tasks."""  # noqa: INP001

import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

executors = [int(contact) for contact in str(os.getenv("CONTACTS")).split()]

tasks = {}


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Привет! Я Telegram Bot кадровой безопасности.")
    if update.effective_user.username not in executors:
        await update.message.reply_text(
            "Представьтесь и укажите данные интересующего лица.\n"
            "Пример: /task Ваше имя и организация. ФИО, ДД.ММ.ГГГГ.",
        )
    else:
        await update.message.reply_text(
            "Отправьте одну из следующих команд:\n"
            "/accept номер задачи - принять задачу в работу\n"
            "Пример: /accept 1\n\n"
            "/result номер задачи - отправить результат выполнения задачи\n"
            "Пример: /result 1 Результат выполнения задачи",
        )


async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    message = update.message.text.split(maxsplit=1)
    if len(message) < 2:
        await update.message.reply_text(
            "Недостаточно данных для выполнения команды.",
        )
        return
    if message[0] == "/task":
        await new_task(update, context)
    elif message[0] == "/accept":
        await accept_task(update, context)
    elif message[0] == "/result":
        await send_result(update, context)
    else:
        await update.message.reply_text("Неизвестная команда.")


async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /task is issued."""
    user = update.effective_user
    message = update.message.text.split(maxsplit=1)

    task_description = message[1].strip()
    task_id = len(tasks) + 1

    tasks[task_id] = {
        "description": task_description,
        "creator": user.id,
        "assignee": None,
    }

    for executor in executors:
        await context.bot.send_message(
            chat_id=executor,
            text=f"Новая задача #{task_id}: {task_description}",
        )

    await update.message.reply_text(
        f"Запрос #{task_id} отправлен исполнителю.",
    )


async def accept_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /accept is issued."""
    user = update.effective_user
    message = update.message.text.split(maxsplit=1)

    try:
        task_id = int(message[1])
    except ValueError:
        await update.message.reply_text("Номер задачи должен быть числом.")
        return

    if task_id not in tasks or tasks[task_id]["assignee"]:
        await update.message.reply_text(
            "Задачи с таким ID не существует или она уже принята в работу.",
        )
        return

    tasks[task_id]["assignee"] = user.id

    for executor in executors:
        await context.bot.send_message(
            chat_id=executor,
            text=f"{user.full_name} принял задачу #{task_id} в работу.",
        )

    await update.message.reply_text(f"Вы приняли задачу #{task_id} в работу.")


async def send_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /result is issued."""
    message = update.message.text.split(maxsplit=1)

    try:
        task_id = int(message[1].split()[0])
    except ValueError:
        await update.message.reply_text("Номер задачи должен быть числом.")
        return

    if task_id not in tasks:
        await update.message.reply_text(
            "Задачи с таким номером не существует или она не принята Вами в работу.",
        )
        return

    result = " ".join(message[1].split()[1:])
    tasks[task_id]["result"] = result

    await context.bot.send_message(
        chat_id=tasks[task_id]["creator"],
        text=f"{result}",
    )

    await update.message.reply_text(
        f"Вы отправили результат выполненной задачи #{task_id}.",
    )

    _ = tasks.pop(task_id)


async def main() -> None:
    """Start the bot."""
    app = ApplicationBuilder().token("TOKEN").build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.COMMAND, msg))

    logging.info("Starting bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())
