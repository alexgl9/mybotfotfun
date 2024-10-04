import os
import logging
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import RetryAfter

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функція для генерації тексту (без змін)
def generate_response(prompt):
    return "клас"

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я Дарина, ваш ШІ-асистент.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    response = generate_response(update.message.text)
    await update.message.reply_text(response)

# Налаштування вебхука з обробкою Flood Control
async def set_webhook_with_retry(application, webhook_url):
    try:
        await application.bot.set_webhook(webhook_url)
        logger.info(f"Вебхук налаштовано на: {webhook_url}")
    except RetryAfter as e:
        logger.warning(f"Flood control: зачекайте {e.retry_after} секунд")
        await asyncio.sleep(e.retry_after)
        await set_webhook_with_retry(application, webhook_url)

# Головна функція
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = f"https://mybotfotfun-production.up.railway.app/{token}"
    
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Встановлення вебхука з обробкою Flood Control
    await set_webhook_with_retry(application, webhook_url)

    logger.info("Бот запущено")

    # Тримаємо бот у вебхуковому режимі
    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        url_path=token,
        webhook_url=webhook_url,
    )

if __name__ == '__main__':
    asyncio.run(main())
