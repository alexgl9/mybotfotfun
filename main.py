import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline, set_seed

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face
generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M')
set_seed(42)  # Для відтворюваності

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я бот, який генерує відповіді на ваші запити.')

# Функція для генерації відповіді
def generate_response(prompt):
    response = generator(prompt, max_length=50, num_return_sequences=1, do_sample=True)
    return response[0]['generated_text'].strip()

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота за ім'ям або юзернеймом, або якщо це особисте повідомлення
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message or update.message.chat.type == 'private':
        # Генеруємо відповідь
        generated_response = generate_response(message)
        await update.message.reply_text(generated_response, reply_to_message_id=update.message.message_id)

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
