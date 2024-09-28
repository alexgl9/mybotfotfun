import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Hugging Face API URL та токен
HF_API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-1.3B"
HF_HEADERS = {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"}

# Функція для звернення до Hugging Face API
def query_huggingface(prompt):
    response = requests.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": prompt})
    return response.json()[0]["generated_text"]

# Функція для відповіді на повідомлення
async def handle_message(update: Update, context):
    user_message = update.message.text
    if "Олєг" in user_message:  # Якщо ім'я "Олєг" у повідомленні
        # Відправляємо повідомлення у Hugging Face API і отримуємо відповідь
        bot_response = query_huggingface(user_message)
        await update.message.reply_text(bot_response)

# Основна функція для старту бота
async def start(update: Update, context):
    await update.message.reply_text("Привіт! Я Олєг, твій AI-бот. Пиши 'Олєг', щоб запитати щось у мене!")

# Старт додатку
if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    # Хендлери для команд та повідомлень
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    application.run_polling()
