import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Отримання токенів
telegram_token = os.getenv("TELEGRAM_TOKEN")
hf_api_token = os.getenv("HF_API_TOKEN")

# URL для Hugging Face API
HF_API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-1.3B"

# Генерація відповіді
def generate_response(prompt):
    headers = {"Authorization": f"Bearer {hf_api_token}"}
    response = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt})
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        return "Error: Unable to get response from model."

# Обробка повідомлень
def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    # Додаємо логіку для тригера на ім'я бота
    if "Олєг" in user_message:  # замініть "Олєг" на ім'я вашого бота
        bot_response = generate_response(user_message)
        update.message.reply_text(bot_response)

# Основна функція
def main():
    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
