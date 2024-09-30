import os
import random
import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from transformers import pipeline
from aiohttp import web
import asyncio

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Ініціалізація моделі Hugging Face DistilGPT-2
try:
    generator = pipeline('text-generation', model='distilgpt2')  # Використовуємо DistilGPT-2
    logger.info("Hugging Face DistilGPT-2 model initialized successfully")
    
    # Тест генерації відповіді
    test_prompt = "Hello, how are you?"
    test_response = generator(test_prompt, max_length=50, num_return_sequences=1, pad_token_id=50256)
    logger.info(f"Test response: {test_response[0]['generated_text']}")

except Exception as e:
    logger.error(f"Failed to initialize Hugging Face model: {str(e)}")
    generator = None

# Функція для генерації відповіді
def generate_response(prompt):
    logger.info(f"Generating response for prompt: {prompt}")
    if generator is None:
        return "Вибачте, я зараз не можу генерувати відповіді."
    try:
        # Використовуємо pad_token_id=50256 для правильного завершення генерації
        response = generator(prompt, max_length=100, num_return_sequences=1, pad_token_id=50256, truncation=True)
        logger.info(f"Generated response: {response[0]['generated_text']}")
        return response[0]['generated_text'].strip()  # Вирізаємо зайві пробіли
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return "Вибачте, сталася помилка при генерації відповіді."

# Змінна для зберігання характеру бота
character_prompt = "Я бот, який відповідає на запитання про життя."  # За замовчуванням

# Обробник команди /start
async def start(update: Update, context):
    logger.info(f"Received /start command from user {update.effective_user.id}")
    await update.message.reply_text('Привіт! Я AI бот, готовий спілкуватися в групі.')

# Обробник команди /set_character
async def set_character(update: Update, context):
    global character_prompt
    if context.args:
        character_prompt = ' '.join(context.args)
        await update.message.reply_text(f"Характер бота змінено на: {character_prompt}")
        logger.info(f"Character prompt set to: {character_prompt}")
    else:
        await update.message.reply_text("Будь ласка, надайте новий характер для бота.")

# Обробник повідомлень
async def handle_message(update: Update, context):
    logger.info(f"Received message from user {update.effective_user.id}: {update.message.text[:20]}...")
    message = update.message.text
    chat_id = update.effective_chat.id
    
    # Отримання username бота
    bot_username = context.bot.username

    try:
        # Перевірка, чи це групове повідомлення
        if update.message.chat.type in ['group', 'supergroup']:
            # Перевірка, чи бот згаданий у повідомленні або це відповідь на повідомлення бота
            if (bot_username and bot_username.lower() in message.lower()) or \
            (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id):
                response = generate_response(message)
                await context.bot.send_message(chat_id=chat_id, text=response, reply_to_message_id=update.message.message_id)
                logger.info(f"Responded to message in group {chat_id}")
            else:
                # Випадкове втручання в розмову
                if random.random() < 0.05:  # 5% шанс втрутитися
                    response = generate_response(message)
                    await context.bot.send_message(chat_id=chat_id, text=response)
                    logger.info(f"Randomly intervened in group {chat_id}")
        else:
            # Обробка особистих повідомлень
            if message.lower().startswith("дарина"):
                response = generate_response(message)
                await context.bot.send_message(chat_id=chat_id, text=response)
                logger.info(f"Responded to direct message from user {update.effective_user.id}")
            else:
                logger.info("Message ignored due to username mention requirements.")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await context.bot.send_message(chat_id=chat_id, text="Вибачте, сталася помилка при обробці повідомлення.")

# Обробник для веб-сервера
async def handle_web_request(request):
    logger.info("Received web request")
    return web.Response(text="Telegram bot is running!")

# Налаштування вебхука
async def setup_webhook(application, webhook_url):
    try:
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        response = await application.bot.setWebhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}, response: {response}")
    except Exception as e:
        logger.error(f"Failed to set webhook: {str(e)}")

# Головна функція
async def main():
    try:
        # Отримання токену з змінних середовища
        telegram_token = os.getenv('TELEGRAM_TOKEN')
        if not telegram_token:
            raise ValueError("TELEGRAM_TOKEN is not set")
        
        logger.info("Starting bot application...")
        # Створення і налаштування застосунку
        application = Application.builder().token(telegram_token).build()

        # Додавання обробників
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("set_character", set_character))  # Обробник для зміни характеру
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Налаштування веб-сервера
        app = web.Application()
        app.router.add_get('/', handle_web_request)

        # Запуск вебхука
        webhook_url = f"https://mybotfotfun.onrender.com/{telegram_token}"  # URL для вебхука
        await setup_webhook(application, webhook_url)

        # Запуск бота і веб-сервера
        async def run_bot():
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            logger.info("Bot polling started")

        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get('PORT', 10000))  # Використання змінної PORT для Render
        site = web.TCPSite(runner, '0.0.0.0', port)
        
        logger.info(f"Starting web server on port {port}")
        await site.start()
        logger.info("Web server started successfully")
        
        await run_bot()
        logger.info("Bot started successfully")
        
        # Тримаємо програму працюючою
        while True:
            await asyncio.sleep(3600)  # Чекаємо годину перед наступною перевіркою
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(main())
