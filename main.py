import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline, set_seed

# Ініціалізація моделі Hugging Face
generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M', use_auth_token=os.getenv('HF_API_TOKEN'))
set_seed(42)  # Для відтворюваності результатів

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я бот і відповідаю на згадки.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота за ім'ям або юзернеймом, або якщо це особисте повідомлення
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message or update.message.chat.type == 'private':
        # Генерація відповіді
        response = generator(message, max_length=50, num_return_sequences=1, truncation=True)[0]['generated_text']
        await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
