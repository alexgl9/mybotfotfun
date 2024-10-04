import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Обробники
async def start(update: Update, context):
    await update.message.reply_text('Бот запущено!')

async def handle_message(update: Update, context):
    await update.message.reply_text('клас')

async def setup_webhook(application):
    # Формуємо URL для вебхука без порту
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/{os.getenv('TELEGRAM_TOKEN')}"
    logger.info(f"Налаштовуємо вебхук на: {webhook_url}")
    
    # Налаштовуємо вебхук
    await application.bot.set_webhook(webhook_url)

async def main():
    # Отримання токена з змінної середовища
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN не знайдено в змінних середовища")
        return

    # Створення і запуск бота
    application = Application.builder().token(token).build()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Налаштовуємо вебхук
    await setup_webhook(application)

    # Запускаємо бота
    await application.start()
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
