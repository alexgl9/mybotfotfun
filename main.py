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
    await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися в групі.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text
    chat_id = update.effective_chat.id
    
    # Отримання username бота
    bot_username = context.bot.username

    # Перевірка, чи це групове повідомлення
    if update.message.chat.type in ['group', 'supergroup']:
        # Перевірка, чи бот згаданий у повідомленні або це відповідь на повідомлення бота
        if (bot_username and bot_username.lower() in message.lower()) or \
           (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id):
            response = generate_response(message)
            await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)
        else:
            # Випадкове втручання в розмову
            if random.random() < 0.05:  # 5% шанс втрутитися
                response = generate_response(message)
                await context.bot.send_message(chat_id=chat_id, text=response)
    else:
        # Обробка особистих повідомлень
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
    
