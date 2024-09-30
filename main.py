import os
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
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face
try:
    model_name = "distilgpt2"
    generator = pipeline('text-generation', model=model_name)
    logger.info("Hugging Face DistilGPT-2 model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Hugging Face model: {str(e)}")
    generator = None

# Функція для генерації відповіді
def generate_response(prompt):
    logger.info(f"Generating response for prompt: {prompt}")
    if generator is None:
        return "Вибачте, я зараз не можу генерувати відповіді."
    try:
        response = generator(prompt, max_length=100, num_return_sequences=1, truncation=True)
        generated_text = response[0]['generated_text'].strip()
        logger.info(f"Generated response: {generated_text}")
        return generated_text
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

    try:
        if (context.bot.username and context.bot.username.lower() in message.lower()) or \
           (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id):
            response = generate_response(message)
            await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)
            logger.info(f"Responded to message in group {chat_id}")
        else:
            logger.info("Message ignored due to missing mention.")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text="Вибачте, сталася помилка при обробці повідомлення.")

# Головна функція
async def main():
    try:
        TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is not set")

        logger.info("Starting bot application...")
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Додавання обробників
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Налаштування вебхука
        webhook_url = f"https://mybotfotfun.onrender.com/{TELEGRAM_TOKEN}"

        async def set_webhook():
            await application.bot.set_webhook(webhook_url)
            logger.info(f"Webhook set to {webhook_url}")

        async def web_app():
            async def webhook_handler(request):
                logger.info("Webhook received")
                data = await request.json()
                update = Update.de_json(data, application.bot)
                await application.update_queue.put(update)
                return web.Response()

            app = web.Application()
            app.router.add_post(f'/{TELEGRAM_TOKEN}', webhook_handler)
            app.router.add_get('/', lambda request: web.Response(text="Telegram bot is running!"))

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8443)))
            await site.start()
            logger.info(f"Web app started on port {os.environ.get('PORT', 8443)}")

        await set_webhook()
        await web_app()
        await application.start()
        logger.info("Bot started successfully")

        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
