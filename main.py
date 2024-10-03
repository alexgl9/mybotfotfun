import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face
generator = pipeline('text-generation', model='distilgpt2', token=os.getenv('HF_API_TOKEN'))

# Функція для відповіді
def generate_response(prompt):
    logger.info(f"Generating response for prompt: {prompt}")
    response = generator(prompt, max_length=50, num_return_sequences=1, truncation=True)
    return response[0]['generated_text'].strip()

# Обробники
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися.')

async def handle_message(update: Update, context):
    message = update.message.text
    response = generate_response(message)
    await update.message.reply_text(response)

# Головна функція
async def main():
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Налаштування вебхука
    webhook_url = f"https://{os.getenv('RAILWAY_PROJECT_NAME')}.railway.app/{os.getenv('TELEGRAM_TOKEN')}"
    logger.info(f"Setting up webhook to {webhook_url}")
    await application.bot.set_webhook(webhook_url)

    # Запуск бота
    await application.initialize()
    await application.start_polling()
    logger.info("Bot started successfully")

if __name__ == '__main__':
    asyncio.run(main())
