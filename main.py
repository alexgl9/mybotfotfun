import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline

# Ініціалізація моделі HuggingFace
generator = pipeline('text-generation', model='gpt2')

# Функція для генерації відповіді
def generate_response(prompt):
    response = generator(prompt, max_length=100, num_return_sequences=1)
    return response[0]['generated_text']

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я Дарина, ваш ШІ-асистент. Як я можу вам допомогти?')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message
    text = message.text.lower()

    # Перевірка, чи згадано бота
    if 'дарина' in text or f'@{context.bot.username}' in text:
        response = generate_response(text)
        await message.reply_text(response)
    elif random.random() < 0.1:  # 10% шанс відповісти на випадкове повідомлення
        response = generate_response(text)
        await message.reply_text(response)

def main():
    # Отримання токена з змінної середовища
    token = os.environ.get('TELEGRAM_TOKEN')
    
    # Створення і запуск бота
    application = Application.builder().token(token).build()
    
    # Додавання обробників
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
