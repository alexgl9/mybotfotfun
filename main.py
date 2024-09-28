import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests

# Увімкнення логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Функція для отримання відповіді з Hugging Face
def get_response_from_hugging_face(prompt):
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
    }
    data = {
        "inputs": prompt,
    }
    response = requests.post("https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-125M", headers=headers, json=data)
    return response.json()

# Функція обробки повідомлень
def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    if "Олєг" in user_message:
        response_text = get_response_from_hugging_face(user_message)
        update.message.reply_text(response_text['generated_text'])  # Адаптуйте це в залежності від формату відповіді

# Основна функція
def main():
    updater = Updater("7248649621:AAEENgDmHh4cUQ1VMaVumbs4WtGbzr2sUSY")
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Привіт! Я бот, готовий до спілкування!")))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
