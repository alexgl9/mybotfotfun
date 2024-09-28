import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Вставте ваш токен Telegram
TELEGRAM_TOKEN = '7248649621:AAEENgDmHh4cUQ1VMaVumbs4WtGbzr2sUSY'
# Вставте ваш токен Hugging Face
HUGGINGFACE_TOKEN = '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'
# Вибрана модель
MODEL_NAME = 'gpt-neo-125M'

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привіт! Я бот на базі ШІ. Чим можу допомогти?')

def respond_to_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    response = generate_response(user_message)
    update.message.reply_text(response)

def generate_response(user_message: str) -> str:
    headers = {
        'Authorization': f'Bearer {HUGGINGFACE_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "inputs": user_message,
        "options": {"use_cache": False}
    }

    response = requests.post(f'https://api-inference.huggingface.co/models/{MODEL_NAME}', headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        return "Вибачте, я не зміг отримати відповідь."

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, respond_to_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
