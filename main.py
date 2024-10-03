import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Отримання токенів з змінних середовища
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RAILWAY_PROJECT_NAME = os.getenv("RAILWAY_PROJECT_NAME")

# Ініціалізація моделі Hugging Face DistilGPT-2
try:
    generator = pipeline('text-generation', model='distilgpt2', use_auth_token=HF_API_TOKEN)
    logger.info("Hugging Face DistilGPT-2 model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Hugging Face model: {str(e)}")
    generator = None

# Функція для генерації відповіді
def generate_response(prompt):
    if generator is None:
        return "Вибачте, я зараз не можу генерувати відповіді."
    try:
        response = generator(prompt, max_length=50, num_return_sequences=1, truncation=True)
        return response[0]['generated_text'].strip()
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "Вибачте, сталася помилка при генерації відповіді."

# Обробники команд
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися.')

async def handle_message(update: Update, context):
    message = update.message.text
    if message.lower().startswith("як справи?") or "дарина" in message.lower() or update.message.reply_to_message:
        response = generate_response(message)
        await update.message.reply_text(response)
    else:
        logger.info("Message ignored due to content.")

# Головна функція
async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Налаштування вебхука
    webhook_url = f"https://{RAILWAY_PROJECT_NAME}.railway.app/{TELEGRAM_TOKEN}"
    logger.info(f"Setting up webhook to {webhook_url}")

    # Встановлення вебхука
    await application.bot.set_webhook(webhook_url)

    # Запуск
    await application.initialize()
    await application.start()
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
