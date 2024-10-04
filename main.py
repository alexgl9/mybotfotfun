import os
import random
import asyncio
import openai  # Коректний імпорт OpenAI
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Встановлюємо ключ OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Стандартна роль
default_role = "дівчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки."
pending_messages = []  # Список для накопичення запитів

# Створення JSONL файлу для запитів
def create_jsonl_file(messages, file_path="batchinput.jsonl"):
    with open(file_path, 'w') as file:
        for i, message in enumerate(messages):
            data = {
                "custom_id": f"request-{i+1}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": f"You are {default_role}."},
                        {"role": "user", "content": message}
                    ]
                }
            }
            file.write(json.dumps(data) + "\n")
    return file_path

# Завантаження файлу з запитами на сервер OpenAI
def upload_batch_file(file_path):
    with open(file_path, "rb") as file:
        batch_input_file = openai.File.create(file=file, purpose="batch")
    return batch_input_file.id

# Створення партії для обробки запитів
def create_batch(batch_file_id):
    batch = openai.Batch.create(
        input_file_id=batch_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    return batch

# Перевірка статусу партії
def check_batch_status(batch_id):
    batch_status = openai.Batch.retrieve(batch_id)
    return batch_status

# Отримання результатів після завершення партії
def get_batch_results(output_file_id):
    file_response = openai.File.content(output_file_id)
    return file_response.text

# Асинхронний процес обробки запитів через Batch API
async def handle_batch_responses():
    while True:
        if len(pending_messages) >= 5:  # Створюємо партію після 5 повідомлень
            file_path = create_jsonl_file(pending_messages)
            batch_file_id = upload_batch_file(file_path)
            batch = create_batch(batch_file_id)
            await asyncio.sleep(10)  # Очікуємо завершення партії
            batch_status = check_batch_status(batch['id'])
            if batch_status['status'] == 'completed':
                results = get_batch_results(batch_status['output_file_id'])
                print("Batch Results: ", results)  # Можна вивести результати або використати їх далі
        await asyncio.sleep(5)  # Перевіряємо кожні 5 секунд

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт! Я Дарина і сьогодні я вся ваша.')

# Обробник повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()

    # Якщо бот згадується по імені або username
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        pending_messages.append(message)
        await update.message.reply_text("Ваш запит буде оброблено незабаром!", reply_to_message_id=update.message.message_id)

# Зміна ролі бота через команду /set
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global default_role
    if context.args:
        default_role = ' '.join(context.args)
        await update.message.reply_text(f"Роль змінено на: {default_role}")
    else:
        await update.message.reply_text("Будь ласка, надайте нову роль.")

# Основна функція для запуску бота
async def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Створюємо задачу для обробки batch відповідей
    asyncio.create_task(handle_batch_responses())

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
