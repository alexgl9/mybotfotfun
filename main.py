import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline
from aiohttp import web
import asyncio

# Ініціалізація моделі Hugging Face
generator = pipeline('text-generation', model='gpt2')

# Функція для генерації відповіді
def generate_response(prompt):
    response = generator(prompt, max_length=100, num_return_sequences=1)
    return response[0]['generated_text']

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт сученьки! Я прийшла сюди щоб вас обсирати')

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text
    chat_id = update.effective_chat.id
    
    # Отримання username бота
    bot_username = context.bot.username

    # Перевірка, чи це групове повідомлення
    if update.message.chat.type in ['group', 'supergroup']:
        # Перевірка, чи бот згаданий у повідомленні або це відповідь на повідомлення бота
        if (bot_username and bot_username.lower() in message.lower()) or \
           (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id):
            response = generate_response(message)
            await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)
        else:
            # Випадкове втручання в розмову
            if random.random() < 0.05:  # 5% шанс втрутитися
                response = generate_response(message)
                await context.bot.send_message(chat_id=chat_id, text=response)
    else:
        # Обробка особистих повідомлень
        response = generate_response(message)
        await context.bot.send_message(chat_id=chat_id, text=response)

# Обробник для веб-сервера
async def handle_web_request(request):
    return web.Response(text="Telegram bot is running!")

# Головна функція
async def main():
    # Отримання токену з змінних середовища
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    
    # Створення і налаштування застосунку
    application = Application.builder().token(telegram_token).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Налаштування веб-сервера
    app = web.Application()
    app.router.add_get('/', handle_web_request)

    # Запуск бота і веб-сервера
    async def run_bot():
        await application.initialize()
        await application.start()
        await application.updater.start_polling()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get('PORT', 10000)))
    
    await asyncio.gather(run_bot(), site.start())

if __name__ == '__main__':
    asyncio.run(main())
