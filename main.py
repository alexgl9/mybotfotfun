import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face
try:
    generator = pipeline('text-generation', model='distilgpt2', token=os.getenv("HF_API_TOKEN"))
    logger.info("Hugging Face DistilGPT-2 model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize model: {str(e)}")
    generator = None

# Функція для генерації відповіді
def generate_response(prompt):
    if generator is None:
        return "Вибачте, я зараз не можу генерувати відповіді."
    response = generator(prompt, max_length=50, num_return_sequences=1, truncation=True)
    return response[0]['generated_text'].strip()

# Обробники
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я AI бот.')

async def handle_message(update: Update, context):
    message = update.message.text
    chat_id = update.effective_chat.id

    # Перевірка, чи це групове повідомлення або особисте
    if message.lower().startswith("дарина") or f"@{context.bot.username}" in message:
        response = generate_response(message)
        await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)

# Головна функція
async def main():
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Ініціалізація
    await application.initialize()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск вебхука
    webhook_url = f"https://{os.getenv('RAILWAY_PROJECT_NAME')}.railway.app/{os.getenv('TELEGRAM_TOKEN')}"
    logger.info(f"Setting up webhook to {webhook_url}")
    await application.bot.set_webhook(webhook_url)

    # Запуск
    await application.start()
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
