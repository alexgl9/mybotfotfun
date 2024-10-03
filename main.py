import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

# Логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Отримання токена з оточення
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Ініціалізація моделі Hugging Face
try:
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2", use_auth_token=HF_API_TOKEN)
    model = AutoModelForCausalLM.from_pretrained("distilgpt2", use_auth_token=HF_API_TOKEN)
    generator = pipeline('text-generation', model=model, tokenizer=tokenizer)
    logger.info("Hugging Face DistilGPT-2 model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Hugging Face model: {str(e)}")
    generator = None

# Функція для відповіді
def generate_response(prompt):
    if generator is None:
        return "Вибачте, я не можу генерувати відповіді."
    response = generator(prompt, max_length=50, num_return_sequences=1, truncation=True)
    return response[0]['generated_text'].strip()

# Обробники
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я AI бот. Як можу допомогти?')

async def handle_message(update: Update, context):
    message = update.message.text

    # Фільтрація повідомлень
    if '?' in message:
        await update.message.reply_text("На питання я не відповідаю.")
        return

    response = generate_response(message)
    await update.message.reply_text(response)

async def help_command(update: Update, context):
    await update.message.reply_text('Використовуйте команди: /start, /help')

# Головна функція
async def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Ініціалізація
    await application.initialize()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск вебхука
    await application.start()
    await application.updater.start_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),  # Використовуємо PORT з оточення
        url_path=TELEGRAM_TOKEN
    )
    application.bot.setWebhook(f"https://bot-d-production.up.railway.app/{TELEGRAM_TOKEN}")

    # Тримаємо програму працюючою
    await application.updater.idle()

if __name__ == '__main__':
    asyncio.run(main())
