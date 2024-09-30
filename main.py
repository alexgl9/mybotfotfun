import os
import logging
import sys
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline
from aiohttp import web
import asyncio

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face GPT-Neo 125M
try:
    generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M', pad_token_id=50256)
    logger.info("Hugging Face GPT-Neo model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Hugging Face model: {str(e)}")
    generator = None

# Функція для генерації відповіді
def generate_response(prompt):
    if generator is None:
        return "Вибачте, я зараз не можу генерувати відповіді."
    try:
        logger.info(f"Generating response for prompt: {prompt}")
        response = generator(prompt, max_length=100, num_return_sequences=1, truncation=True)
        return response[0]['generated_text'].strip()
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "Вибачте, сталася помилка при генерації відповіді."

# Обробник команди /start
async def start(update: Update, context):
    try:
        logger.info(f"Received /start command from user {update.effective_user.id}")
        await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися в групі.')
    except Exception as e:
        logger.error(f"Error in /start command: {str(e)}")

# Обробник повідомлень
async def handle_message(update: Update, context):
    try:
        if not update.message:
            logger.warning("No message to process")
            return
        
        logger.info(f"Received message from user {update.effective_user.id}: {update.message.text[:20]}...")
        message = update.message.text
        chat_id = update.effective_chat.id
        bot_username = context.bot.username

        # Відповідь, якщо бот згаданий або відповідь на його повідомлення
        if (bot_username and bot_username.lower() in message.lower()) or \
           (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id):
            response = generate_response(message)
            await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)
            logger.info(f"Responded to message in group {chat_id}")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Вибачте, сталася помилка при обробці повідомлення.")

# Налаштування веб-хука
def setup_webhook(telegram_token):
    try:
        webhook_url = f"https://mybotfotfun.onrender.com/{telegram_token}"  # URL для веб-хука
        response = requests.post(f"https://api.telegram.org/bot{telegram_token}/setWebhook", data={'url': webhook_url})

        if response.status_code == 200:
            logger.info(f"Webhook set successfully: {webhook_url}")
        else:
            logger.error(f"Failed to set webhook: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error setting up webhook: {str(e)}")

# Обробник для веб-хука
async def webhook(request):
    try:
        # Отримання тіла запиту
        update_data = await request.json()
        logger.info(f"Webhook received: {update_data}")

        # Обробка оновлення
        update = Update.de_json(update_data, bot)
        await bot.process_update(update)

        return web.Response()
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        return web.Response(status=500)

# Головна функція для запуску бота
async def main():
    try:
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN is not set")

        # Створення застосунку
        application = Application.builder().token(telegram_token).build()

        # Додавання обробників
        application.add_handler(CommandHandler("start", start))

        # Налаштування веб-хука
        setup_webhook(telegram_token)

        # Ініціалізація бота перед стартом
        await application.initialize()

        # Налаштування веб-сервера для обробки веб-хуків
        app = web.Application()
        app.router.add_post(f"/{telegram_token}", webhook)  # Обробка веб-хуків

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get('PORT', 10000))  # Використання порту для веб-хука
        site = web.TCPSite(runner, '0.0.0.0', port)

        logger.info(f"Starting webhook on port {port}")
        await site.start()

        logger.info("Bot started successfully with webhooks")
        await application.start()

        # Тримаємо програму працюючою
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
