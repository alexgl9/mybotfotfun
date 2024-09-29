import logging
import os
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from transformers import pipeline

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Hugging Face API
HF_API_TOKEN = os.getenv('HF_API_TOKEN')
generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M', token=HF_API_TOKEN)

# Команда start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я чат-бот на базі штучного інтелекту.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    user_message = update.message.text
    logger.info(f"Отримано повідомлення: {user_message}")
    
    # Генерація відповіді
    response = generator(user_message, max_length=100, do_sample=True)[0]['generated_text']
    logger.info(f"Відповідь AI: {response}")

    await update.message.reply_text(response)

# Основна функція
def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    application = ApplicationBuilder().token(TOKEN).build()

    # Команди
    application.add_handler(CommandHandler("start", start))
    
    # Повідомлення
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    logger.info("Бот запущений...")
    application.run_polling()

if __name__ == '__main__':
    main()
