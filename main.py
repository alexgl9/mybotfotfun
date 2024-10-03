import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face
generator = pipeline('text-generation', model='gpt2')

# Функція для відповіді
def generate_response(prompt):
    response = generator(prompt, max_length=50, num_return_sequences=1)
    return response[0]['generated_text'].strip()

# Обробники
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я AI бот.')

async def handle_message(update: Update, context):
    message = update.message.text
    response = generate_response(message)
    await update.message.reply_text(response)

# Головна функція
async def main():
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await application.start()
    await application.updater.start_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
