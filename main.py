import os
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

# Встановлюємо рівень логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Функція для обробки текстових повідомлень
def handle_message(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received message: {update.message.text}")  # Логування отриманого повідомлення
    if 'Олєг' in update.message.text:
        response_text = get_ai_response(update.message.text)
        update.message.reply_text(response_text)

def get_ai_response(prompt):
    # Тут викликається Hugging Face API
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}",
    }
    payload = {
        "inputs": prompt,
        "options": {"use_cache": False},
    }
    
    response = requests.post("https://api-inference.huggingface.co/models/gpt-neo-125M", headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()[0]['generated_text']  # Можливо, потрібно адаптувати
    else:
        logger.error(f"Error from Hugging Face API: {response.status_code}, {response.text}")
        return "Вибачте, я не можу відповісти."

def main():
    TELEGRAM_TOKEN = '7248649621:AAEENgDmHh4cUQ1VMaVumbs4WtGbzr2sUSY'  # Ваш токен Telegram

    updater = Updater(TELEGRAM_TOKEN)

    dp = updater.dispatcher

    # Додаємо обробник для текстових повідомлень
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запускаємо бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
