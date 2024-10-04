import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline, set_seed

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face
try:
    generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M', device=-1)  # Використовуємо CPU
    set_seed(42)  # Для відтворюваності результатів
    logger.info("Модель успішно завантажена")
except Exception as e:
    logger.error(f"Помилка при завантаженні моделі: {e}")
    raise

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я бот і відповідаю на згадки.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message:
        logger.info("Згадка бота виявлена.")
        response = generate_response(message)
        await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
    elif update.message.chat.type == 'private':
        logger.info("Отримано особисте повідомлення.")
        response = generate_response(message)
        await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

def generate_response(prompt):
    try:
        response = generator(prompt, max_length=50, num_return_sequences=1, truncation=True)
        return response[0]['generated_text'].strip()
    except Exception as e:
        logger.error(f"Помилка при генерації відповіді: {e}")
        return "Вибачте, не можу згенерувати відповідь."

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
