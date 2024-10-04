import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функція для генерації тексту з Hugging Face
def generate_response(prompt):
    api_token = os.getenv("HF_API_TOKEN")
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_length": 100, "do_sample": True, "temperature": 0.7},
    }
    response = requests.post(
        "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-125M", 
        headers=headers, 
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        logger.error(f"Помилка: {response.status_code}, {response.text}")
        return "Вибачте, виникла помилка при генерації відповіді."

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я Дарина, ваш ШІ-асистент.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text
    response = generate_response(message)
    await update.message.reply_text(response)

# Головна функція
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    webhook_url = f"https://mybotfotfun-production.up.railway.app/{token}"
    
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Встановлення вебхука
    await application.bot.set_webhook(webhook_url)

    logger.info(f"Вебхук налаштовано на: {webhook_url}")
    logger.info("Бот запущено")

    # Тримаємо бот у вебхуковому режимі
    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        url_path=token,
        webhook_url=webhook_url,
    )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
