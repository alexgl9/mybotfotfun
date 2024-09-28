import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import os

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваш токен
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Токен Hugging Face

# Функція для генерації відповіді за допомогою Hugging Face
def generate_response(message: str) -> str:
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}"
    }
    data = {
        "inputs": message
    }
    response = requests.post("https://api-inference.huggingface.co/models/gpt2", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        return "Вибачте, я не зміг згенерувати відповідь."

# Функція для обробки текстових повідомлень
def reply(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text  # Отримуємо текст повідомлення
    logger.info(f"Received message: {user_message}")  # Логування отриманого повідомлення

    # Генеруємо відповідь
    response = generate_response(user_message)
    update.message.reply_text(response)  # Відповідаємо користувачу

# Головна функція, яка запускає бота
def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)

    # Отримуємо диспетчер для реєстрації обробників
    dispatcher = updater.dispatcher

    # Регистрируем обработчики
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))

    # Запускаємо бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
