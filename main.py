import os
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Налаштування OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')  # Твій OpenAI API ключ

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я бот, і я можу відповідати на твої запитання.')

# Генерація відповіді за допомогою OpenAI
async def generate_response(message_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Використовуємо модель ChatGPT
        messages=[
            {"role": "user", "content": message_text}
        ],
        max_tokens=50
    )
    return response['choices'][0]['message']['content']

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота за ім'ям або юзернеймом, або якщо це особисте повідомлення
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message or update.message.chat.type == 'private':
        await update.message.reply_text('Генерую відповідь...')
        response_text = await generate_response(message)
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)

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
