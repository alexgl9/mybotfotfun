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
    # Формуємо URL для вебхука
    webhook_url = f"https://{os.getenv('RAILWAY_STATIC_URL')}:{os.getenv('PORT', 8443)}/{os.getenv('TELEGRAM_TOKEN')}"
    print(f"Webhook URL: {webhook_url}")
    logger.info(f"Налаштовуємо вебхук на: {webhook_url}")
    await application.bot.set_webhook(webhook_url)

async def main():
    # Створення і запуск бота
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Налаштовуємо вебхук
    await setup_webhook(application)

    # Запускаємо бота
    await application.start()
    await application.updater.start_webhook(listen="0.0.0.0", port=int(os.getenv('PORT', 8443)))
    await application.updater.idle()

if __name__ == '__main__':
    asyncio.run(main())
