import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import openai

# Ініціалізація OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Генерація відповіді
async def generate_response(message: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": message}
        ],
        max_tokens=100
    )
    return response['choices'][0]['message']['content']

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я бот і відповідаю на твої питання.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота за ім'ям або юзернеймом, або якщо це особисте повідомлення
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message or update.message.chat.type == 'private':
        await update.message.reply_text('Генерую відповідь...')
        response_text = await generate_response(message)
        await update.message.reply_text(response_text)

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
