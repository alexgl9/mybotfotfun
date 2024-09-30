import os
import random
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from aiohttp import web
import asyncio

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Отримання токенів з змінних середовища
HF_API_TOKEN = os.getenv('HF_API_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PORT = int(os.getenv('PORT', 10000))

# Ініціалізація моделі Hugging Face DistilGPT-2
try:
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2", token=HF_API_TOKEN)
    model = AutoModelForCausalLM.from_pretrained("distilgpt2", token=HF_API_TOKEN)
    generator = pipeline('text-generation', model=model, tokenizer=tokenizer)
    logger.info("Hugging Face DistilGPT-2 model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Hugging Face model: {str(e)}")
    generator = None

# Функція для генерації відповіді
def generate_response(prompt):
    if generator is None:
        return "Вибачте, я не можу генерувати відповіді."
    try:
        response = generator(prompt, max_length=100, num_return_sequences=1, truncation=True)
        return response[0]['generated_text'].strip()
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "Сталася помилка при генерації відповіді."

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text
    chat_id = update.effective_chat.id
    bot_username = context.bot.username

    if bot_username.lower() in message.lower() or "Дарина" in message:
        response = generate_response(message)
        await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)

# Головна функція
async def main():
    try:
        if not TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is not set")
        
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Додавання обробників
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Встановлення вебхука
        webhook_url = f"https://mybotfotfun.onrender.com/{TELEGRAM_TOKEN}"
        await application.bot.set_webhook(webhook_url)

        # Налаштування веб-сервера
        app = web.Application()
        app.router.add_post(f'/{TELEGRAM_TOKEN}', lambda request: application.update_queue.put(
            Update.de_json(data=await request.json(), bot=application.bot)
        ))
        app.router.add_get('/', lambda request: web.Response(text="Telegram bot is running!"))

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', PORT)
        await site.start()

        # Тримаємо програму працюючою
        while True:
            await asyncio.sleep(3600)

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
