"""Telegram Bot to manage tasks."""

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Список контактов, которым будут рассылаться задачи
contacts = [
    'contact_id_1',  # Идентификатор контакта 1
    'contact_id_2',  # Идентификатор контакта 2
]

# Словарь для хранения задач и их статусов
tasks = {}

async def start(update: Update, context):
    await update.message.reply_text('Привет! Я помогу вам управлять задачами.')

async def help_command(update: Update, context):
    await update.message.reply_text('Доступны следующие команды:\n'
                                    '/new_task - создать новую задачу\n'
                                    '/my_tasks - посмотреть свои текущие задачи\n'
                                    '/accept_task - принять задачу в работу\n'
                                    '/submit_result - отправить результат выполненной задачи')

async def new_task(update: Update, context):
    user = update.effective_user
    message = update.message.text.split(maxsplit=1)
    
    if len(message) == 1:
        await update.message.reply_text('Пожалуйста, введите текст новой задачи после команды /new_task.')
        return
    
    task_description = message[1].strip()
    task_id = len(tasks) + 1
    
    tasks[task_id] = {
        'description': task_description,
        'creator': user.id,
        'assignee': None,
        'result': None
    }
    
    for contact in contacts:
        await context.bot.send_message(chat_id=contact, text=f'Новая задача #{task_id}: {task_description}')
        
    await update.message.reply_text(f'Задача #{task_id} создана и разослана всем контактам.')

async def my_tasks(update: Update, context):
    user = update.effective_user
    assigned_tasks = []
    created_tasks = []
    
    for task_id, task in tasks.items():
        if task['creator'] == user.id:
            created_tasks.append((task_id, task))
        elif task['assignee'] == user.id:
            assigned_tasks.append((task_id, task))
            
    response = ''
    if created_tasks:
        response += 'Созданные вами задачи:\n'
        for task_id, task in created_tasks:
            response += f'#{task_id}: {task["description"]}\n'
    
    if assigned_tasks:
        response += '\nВаши текущие задачи:\n'
        for task_id, task in assigned_tasks:
            response += f'#{task_id}: {task["description"]}\n'
    
    if not response:
        response = 'У вас нет текущих задач.'
    
    await update.message.reply_text(response)

async def accept_task(update: Update, context):
    user = update.effective_user
    message = update.message.text.split(maxsplit=1)
    
    if len(message) == 1:
        await update.message.reply_text('Пожалуйста, укажите номер задачи после команды /accept_task.')
        return
    
    try:
        task_id = int(message[1])
    except ValueError:
        await update.message.reply_text('Номер задачи должен быть числом.')
        return
    
    if task_id not in tasks or tasks[task_id]['assignee']:
        await update.message.reply_text('Задачи с таким номером не существует или она уже принята в работу.')
        return
    
    tasks[task_id]['assignee'] = user.id
    
    for contact in contacts:
        await context.bot.send_message(chat_id=contact, text=f'{user.full_name} принял задачу #{task_id} в работу.')
    
    await update.message.reply_text(f'Вы приняли задачу #{task_id} в работу.')

async def submit_result(update: Update, context):
    user = update.effective_user
    message = update.message.text.split(maxsplit=1)
    
    if len(message) == 1:
        await update.message.reply_text('Пожалуйста, укажите номер задачи и результат после команды /submit_result.')
        return
    
    try:
        task_id = int(message[1].split()[0])
    except ValueError:
        await update.messag...