import os
import random
import logging
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline, set_seed

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ініціалізація моделі HuggingFace
try:
    # Використовуємо DistilGPT-2 для меншого навантаження на хостинг
    generator = pipeline('text-generation', model='distilgpt2', device=-1)  # використовуємо CPU
    set_seed(42)  # для відтворюваності результатів
    logger.info("Модель успішно завантажена")
except Exception as e:
    logger.error(f"Помилка при завантаженні моделі: {e}")
    raise

# Функція для генерації відповіді з оптимізацією параметрів
def generate_response(prompt):
    try:
        response = generator(prompt, max_length=50, num_return_sequences=1, do_sample=True, temperature=0.7, top_p=0.9)
        return response[0]['generated_text'].strip()
    except Exception as e:
        logger.error(f"Помилка при генерації відповіді: {e}")
        return "Вибачте, у мене виникли труднощі з генерацією відповіді."

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я Дарина, ваш ШІ-асистент. Як я можу вам допомогти?')
    logger.info(f"Бот запущено користувачем {update.effective_user.id}")

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message
    if message is None or message.text is None:
        logger.warning("Отримано порожнє повідомлення")
        return

    text = message.text.lower()
    logger.debug(f"Отримано повідомлення: {text[:50]}...")

    try:
        start_time = time.time()  # Записуємо час початку
        # Перевірка, чи згадано бота
        if 'дарина' in text or (context.bot.username and f'@{context.bot.username.lower()}' in text):
            logger.info("Виявлено згадку бота")
            response = generate_response(text)
            logger.info(f"Згенерована відповідь: {response[:50]}...")
            await message.reply_text(response)
            logger.info(f"Відповідь надіслано на згадку бота: {text[:20]}...")
        elif message.chat.type == 'private' or random.random() < 0.1:  # Завжди відповідаємо в особистих повідомленнях або з 10% шансом в групах
            logger.info("Вибрано для відповіді")
            response = generate_response(text)
            logger.info(f"Згенерована відповідь: {response[:50]}...")
            await message.reply_text(response)
            logger.info(f"Відповідь надіслано: {text[:20]}...")
        else:
            logger.info("Повідомлення проігноровано")
        logger.info(f"Час обробки запиту: {time.time() - start_time:.2f} секунд")
    except Exception as e:
        logger.error(f"Помилка при обробці повідомлення: {e}", exc_info=True)
        await message.reply_text("Вибачте, сталася помилка при обробці вашого повідомлення.")

def main():
    # Отримання токена з змінної середовища
    token = os.environ.get('TELEGRAM_TOKEN')
    if not token:
        logger.error("TELEGRAM_TOKEN не знайдено в змінних середовища")
        return

    # Створення і запуск бота
    try:
        application = Application.builder().token(token).build()
        
        # Додавання обробників
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запуск бота
        logger.info("Бот запускається...")
        application.run_polling()
    except Exception as e:
        logger.error(f"Помилка при запуску бота: {e}", exc_info=True)

if __name__ == '__main__':
    main()
