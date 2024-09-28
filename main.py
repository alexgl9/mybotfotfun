import logging
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Встановлення логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Ваш токен Telegram і токен Hugging Face
TELEGRAM_TOKEN = '7248649621:AAEENgDmHh4cUQ1VMaVumbs4WtGbzr2sUSY'
HUGGING_FACE_TOKEN = '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'
MODEL_NAME = 'gpt-neo-125M'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привіт! Я бот на базі штучного інтелекту. Як я можу вам допомогти?')

def generate_response(message: str) -> str:
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": message,
    }
    response = requests.post(f"https://api-inference.huggingface.co/models/{MODEL_NAME}", headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        logging.error(f"Error from Hugging Face API: {response.status_code} - {response.text}")
        return "Вибачте, я не зміг відповісти на ваше питання."

def respond_to_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    logging.info(f'Received message: {user_message}')  # Логування отриманого повідомлення
    response = generate_response(user_message)
    update.message.reply_text(response)

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, respond_to_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
