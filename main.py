import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Обробники
async def start(update: Update, context):
    await update.message.reply_text('Бот запущено!')

async def handle_message(update: Update, context):
    await update.message.reply_text('клас')

async def main():
    # Отримання токена з змінної середовища
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.error("TELEGRAM_TOKEN не знайдено в змінних середовища")
        return

    # Ініціалізація об'єкта Application
    application = Application.builder().token(token).build()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаємо бота
    await application.initialize()  # Додати ініціалізацію
    logger.info("Бот запущено на polling")
    
    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
