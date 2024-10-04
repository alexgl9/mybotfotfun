import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import RetryAfter
import asyncio

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функція для відповіді
def generate_response(prompt):
    return "клас"

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я Дарина, ваш ШІ-асистент.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    response = generate_response(update.message.text)
    await update.message.reply_text(response)

# Функція для налаштування вебхука
async def setup_webhook(application):
    token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/{token}"
    try:
        await application.bot.set_webhook(webhook_url)
        logger.info(f"Вебхук налаштовано на: {webhook_url}")
    except RetryAfter as e:
        logger.warning(f"Flood control: зачекайте {e.retry_after} секунд")
        await asyncio.sleep(e.retry_after)
        await setup_webhook(application)

# Головна функція
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    port = int(os.getenv('PORT', 8443))

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Ініціалізація бота
    await application.initialize()

    # Встановлення вебхука
    await setup_webhook(application)

    logger.info("Бот запущено")

    # Запуск вебсервера
    await application.start()
    await application.start_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=token
    )
    
    await application.updater.idle()

if __name__ == '__main__':
    asyncio.run(main())
