"""Telegram Bot to manage tasks."""  # noqa: INP001

import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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
    keyboard = [
        [
            InlineKeyboardButton("Помощь", callback_data="help"),
        ],
    ]
    await update.message.reply_text(
        "Привет! Это Telegram бот кадровой безопасности банка. \n"
        "Чтобы узнать доступные команды, нажмите на кнопку Помощь.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    if update.effective_user.username not in executors:
        keyboard = [
            [
                InlineKeyboardButton("Новая задача", callback_data="new_task"),
            ],
        ]
        await update.message.reply_text(
            "Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [
            [
                InlineKeyboardButton("Принять задачу", callback_data="accept_task"),
                InlineKeyboardButton(
                    "Отправить результат", callback_data="send_result"
                ),
            ],
        ]
        await update.message.reply_text(
            "Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /new_task is issued."""
    user = update.effective_user
    message = update.message.text.split(maxsplit=1)

    if len(message) == 1:
        await update.message.reply_text(
            "Пожалуйста, введите текст новой задачи после команды /new_task.",
        )
        return

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
        f"Задача #{task_id} создана и отправлена исполнителям.",
    )


async def accept_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /accept_task is issued."""
    user = update.effective_user
    message = update.message.text.split(maxsplit=1)

    if len(message) == 1:
        await update.message.reply_text(
            "Пожалуйста, укажите номер задачи после команды /accept_task.",
        )
        return

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
    """Send a message when the command /send_result is issued."""
    message = update.message.text.split(maxsplit=1)

    if len(message) == 1:
        await update.message.reply_text(
            "Пожалуйста, укажите ID задачи и результат после команды /send_result.",
        )
        return

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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new_task", new_task))
    app.add_handler(CommandHandler("accept_task", accept_task))
    app.add_handler(CommandHandler("send_result", send_result))

    logging.info("Starting bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    asyncio.run(main())
