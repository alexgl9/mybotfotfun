import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я бот і відповідаю словом "клас" на згадки.')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота за ім'ям або юзернеймом, або якщо це особисте повідомлення
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message or update.message.chat.type == 'private':
        await update.message.reply_text('клас', reply_to_message_id=update.message.message_id)

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
