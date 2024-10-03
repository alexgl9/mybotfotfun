import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline, set_seed
from huggingface_hub import login

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Аутентифікація в Hugging Face
hf_token = os.environ.get('HF_API_TOKEN')
if hf_token:
    login(hf_token)
    logger.info("Успішна аутентифікація в Hugging Face")
else:
    logger.warning("HF_API_TOKEN не знайдено. Аутентифікація не виконана.")

# Ініціалізація моделі HuggingFace
try:
    generator = pipeline('text-generation', model='gpt2', device=-1)  # використовуємо CPU
    set_seed(42)  # для відтворюваності результатів
    logger.info("Модель успішно завантажена")
except Exception as e:
    logger.error(f"Помилка при завантаженні моделі: {e}")
    raise

# Функція для генерації відповіді
def generate_response(prompt):
    try:
        response = generator(prompt, max_length=100, num_return_sequences=1, do_sample=True)
        return response[0]['generated_text']
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
    text = message.text.lower()

    try:
        # Перевірка, чи згадано бота
        if 'дарина' in text or f'@{context.bot.username}' in text:
            response = generate_response(text)
            await message.reply_text(response)
            logger.info(f"Відповідь на згадку бота: {text[:20]}...")
        elif random.random() < 0.1:  # 10% шанс відповісти на випадкове повідомлення
            response = generate_response(text)
            await message.reply_text(response)
            logger.info(f"Випадкова відповідь на: {text[:20]}...")
    except Exception as e:
        logger.error(f"Помилка при обробці повідомлення: {e}")
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
        logger.error(f"Помилка при запуску бота: {e}")

if __name__ == '__main__':
    main()
