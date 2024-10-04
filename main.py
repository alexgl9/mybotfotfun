import os
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Ініціалізація OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт! Я бот і відповідаю на твої питання.')

# Генерація відповіді за допомогою OpenAI
async def generate_response(message: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",  # Використовуйте свою модель тут
            messages=[
                {"role": "user", "content": message}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating response: {e}")
        return "На жаль, сталася помилка при генерації відповіді."

# Обробник повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    await update.message.reply_text("Генерую відповідь...")

    response_text = await generate_response(message)
    await update.message.reply_text(response_text)

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    application = Application.builder().token(token).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
