import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline
from aiohttp import web
import asyncio

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face
generator = pipeline('text-generation', model='gpt2')

# Функція для генерації відповіді
def generate_response(prompt):
    response = generator(prompt, max_length=100, num_return_sequences=1)
    return response[0]['generated_text']

# Обробник команди /start
async def start(update: Update, context):
    logger.info(f"Received /start command from user {update.effective_user.id}")
    await update.message.reply_text('Привіт сученьки! Я готова. давайте ригайте свої ригачки')

# Обробник повідомлень
async def handle_message(update: Update, context):
    logger.info(f"Received message from user {update.effective_user.id}: {update.message.text[:20]}...")
    message = update.message.text
    chat_id = update.effective_chat.id
    
    # Отримання username бота
    bot_username = context.bot.username

    # Перевірка, чи це групове повідомлення
    if update.message.chat.type in ['group', 'supergroup']:
        # Перевірка, чи бот згаданий у повідомленні або це відповідь на повідомлення бота
        if (bot_username and bot_username.lower() in message.lower()) or \
           (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id):
            response = generate_response(message)
            await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)
            logger.info(f"Responded to message in group {chat_id}")
        else:
            # Випадкове втручання в розмову
            if random.random() < 0.05:  # 5% шанс втрутитися
                response = generate_response(message)
                await context.bot.send_message(chat_id=chat_id, text=response)
                logger.info(f"Randomly intervened in group {chat_id}")
    else:
        # Обробка особистих повідомлень
        response = generate_response(message)
        await context.bot.send_message(chat_id=chat_id, text=response)
        logger.info(f"Responded to direct message from user {update.effective_user.id}")

# Обробник для веб-сервера
async def handle_web_request(request):
    logger.info("Received web request")
    return web.Response(text="Telegram bot is running!")

# Головна функція
async def main():
    try:
        # Отримання токену з змінних середовища
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN is not set")
        
        logger.info("Starting bot application...")
        # Створення і налаштування застосунку
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
            await application.updater.start_polling()
            logger.info("Bot polling started")

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get('PORT', 10000))
        site = web.TCPSite(runner, '0.0.0.0', port)
        
        logger.info(f"Starting web server on port {port}")
        await asyncio.gather(run_bot(), site.start())
        logger.info("Bot and web server started successfully")
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
