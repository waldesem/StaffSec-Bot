"""Telegram Bot to manage tasks."""

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

executors = list(str(os.getenv("EXECUTORS")).split())

tasks = {}

HELLO = "Привет, я бот для управления запросами. Для начала работы напишите /start"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    if update.effective_user.username not in executors:
        await update.message.reply_text(
            "Представьтесь и укажите данные интересующего лица.\n"
            "Пример: Ваше имя и организация. ФИО, ДД.ММ.ГГГГ. Комментарии.",
        )
    else:
        await update.message.reply_text(
            "Чтобы принять задачу в работу отправьте команду:\n"
            "/accept ID задачи. Пример: /accept 1\n\n"
            "Чтобы отправить ответ на запрос напишите в чат ID запроса и ответ.\n",
        )


async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the Запрос is issued."""
    task_id = len(tasks) + 1

    tasks[task_id] = {
        "description": update.message.text,
        "creator": update.effective_user.id,
        "assignee": None,
    }

    for executor in executors:
        await context.bot.send_message(
            chat_id=executor,
            text=f"Новая задача #{task_id}: {update.message.text}",
        )

    await update.message.reply_text(
        f"Запрос #{task_id} отправлен исполнителю.",
    )


async def accept_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /accept is issued."""
    user = update.effective_user
    try:
        task_id = int(context.args[0])
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
    """Send a message when the Ответ is issued."""
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
    app.add_handler(CommandHandler("accept", accept_task))
    app.add_handler(MessageHandler(filters.User(executors), send_result))
    app.add_handler(MessageHandler(filters.TEXT, new_task))

    logging.info("Starting bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())
