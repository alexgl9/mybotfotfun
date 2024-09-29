import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline

# Ініціалізація моделі Hugging Face
generator = pipeline('text-generation', model='gpt2')

# Функція для генерації відповіді
def generate_response(prompt):
    response = generator(prompt, max_length=100, num_return_sequences=1)
    return response[0]['generated_text']

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text
    chat_id = update.effective_chat.id

    # Перевірка, чи бот згаданий у повідомленні
    if context.bot.username.lower() in message.lower():
        response = generate_response(message)
        await context.bot.send_message(chat_id=chat_id, text=response)
    else:
        # Випадкове втручання в розмову
        if random.random() < 0.1:  # 10% шанс втрутитися
            response = generate_response(message)
            await context.bot.send_message(chat_id=chat_id, text=response)

# Головна функція
def main():
    # Отримання токену з змінних середовища
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    
    # Створення і налаштування застосунку
    application = Application.builder().token(telegram_token).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
    
