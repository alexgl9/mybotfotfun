import os
import random
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import json

# Ініціалізація OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# Стандартна роль
default_role = "дівчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки."
pending_messages = []  # Для зберігання запитів

# Створення JSONL файлу
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

# Завантаження файлу з запитами
def upload_batch_file(file_path):
    with open(file_path, "rb") as file:
        batch_input_file = client.files.create(file=file, purpose="batch")
    return batch_input_file.id

# Створення партії
def create_batch(batch_file_id):
    batch = client.batches.create(
        input_file_id=batch_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    return batch

# Перевірка статусу партії
def check_batch_status(batch_id):
    batch_status = client.batches.retrieve(batch_id)
    return batch_status

# Отримання результатів після завершення партії
def get_batch_results(output_file_id):
    file_response = client.files.content(output_file_id)
    return file_response.text

# Асинхронний обробник партій
async def handle_batch_responses():
    while True:
        if len(pending_messages) >= 5:  # Створюємо партію після 5 повідомлень
            file_path = create_jsonl_file(pending_messages)
            batch_file_id = upload_batch_file(file_path)
            batch = create_batch(batch_file_id)
            await asyncio.sleep(10)  # Чекаємо 10 секунд для обробки партії
            batch_status = check_batch_status(batch['id'])
            if batch_status['status'] == 'completed':
                results = get_batch_results(batch_status['output_file_id'])
                # Обробка результатів
        await asyncio.sleep(5)  # Перевіряємо кожні 5 секунд

# Запуск партійного процесу
asyncio.create_task(handle_batch_responses())

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт сучєчькі. Я Дарина і сьогодні я вся ваша.')

# Обробник повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()
    chat_id = update.message.chat_id

    if 'дарина' in message or f"@{context.bot.username.lower()}" in message:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        pending_messages.append(message)
        await update.message.reply_text("Ваш запит буде оброблено незабаром!", reply_to_message_id=update.message.message_id)

# Задання ролі для бота
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global default_role
    if context.args:
        default_role = ' '.join(context.args)
        await update.message.reply_text(f"Роль змінено на: {default_role}")
    else:
        await update.message.reply_text("Будь ласка, надайте нову роль.")

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
