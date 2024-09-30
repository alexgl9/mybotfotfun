мimport os
import random
import logging
import sys
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

# Ініціалізація моделі Hugging Face DistilGPT-2
try:
    generator = pipeline('text-generation', model='distilgpt2')  # Використовуємо DistilGPT-2
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

# Обробник команди /start
async def start(update: Update, context):
    logger.info(f"Received /start command from user {update.effective_user.id}")
    await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися в групі.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    logger.info(f"Received message from user {update.effective_user.id}: {update.message.text[:20]}...")
    message = update.message.text
    chat_id = update.effective_chat.id
    bot_username = context.bot.username

    try:
        # Перевірка на використання імені бота або "Дарина"
        if ('@' + bot_username.lower() in message.lower()) or ('Дарина' in message):
            response = generate_response(message)
            await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)
            logger.info(f"Responded to message in group {chat_id}")
        else:
            logger.info("Bot was not mentioned, skipping...")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text="Вибачте, сталася помилка при обробці повідомлення.")

# Обробник для веб-сервера
async def handle_web_request(request):
    logger.info("Received web request")
    return web.Response(text="Telegram bot is running!")

# Головна функція
async def main():
    try:
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        webhook_url = os.getenv('WEBHOOK_URL')
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN is not set")
        if not webhook_url:
            raise ValueError("WEBHOOK_URL is not set")
        
        logger.info("Starting bot application...")
        application = Application.builder().token(telegram_token).build()

        # Додавання обробників
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Налаштування веб-сервера
        app = web.Application()
        app.router.add_get('/', handle_web_request)

        # Запуск бота і веб-сервера
        async def run_bot():
            await application.initialize()
            await application.start()
            await application.updater.start_webhook(listen="0.0.0.0", port=8443, webhook_url=webhook_url)
            logger.info("Bot webhook started")

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get('PORT', 8443))
        site = web.TCPSite(runner, '0.0.0.0', port)
        
        logger.info(f"Starting web server on port {port}")
        await site.start()
        
        await run_bot()
        logger.info("Bot started successfully")
        
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
