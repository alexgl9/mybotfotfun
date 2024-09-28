import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Отримання токенів
telegram_token = os.getenv("TELEGRAM_TOKEN")
hf_api_token = os.getenv("HF_API_TOKEN")

# URL для Hugging Face API
HF_API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-1.3B"

# Функція для запиту до Hugging Face API
def query_hf(payload):
    headers = {"Authorization": f"Bearer {hf_api_token}"}
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()

# Генерація відповіді
def generate_response(prompt):
    data = query_hf({"inputs": prompt})
    if "error" in data:
        return "Model is loading, try again later."
    return data[0]["generated_text"]

# Відповідь на команду /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привіт! Я бот на базі AI. Спитай мене що завгодно!')

# Обробка повідомлень
def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    bot_response = generate_response(user_message)
    update.message.reply_text(bot_response)

# Основна функція
def main():
    # Налаштування бота
    updater = Updater(telegram_token)

    dispatcher = updater.dispatcher

    # Обробка команд і повідомлень
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
