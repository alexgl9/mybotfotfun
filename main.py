import os
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import openai

# Ініціалізація OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Змінна для ролі
role = "Дівчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки."

# Обробник команди /start
async def start(update: Update, context):
    await update.message.reply_text('Привіт! Я бот Дарина, готова відповісти на твої питання!')

# Обробник команди /set
async def set_role(update: Update, context):
    global role
    if context.args:
        role = ' '.join(context.args)
        await update.message.reply_text(f'Роль змінено на: {role}')
    else:
        await update.message.reply_text('Будь ласка, введіть роль після команди /set.')

# Генерація відповіді з OpenAI
async def generate_response(message):
    try:
        response = await openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

# Обробник повідомлень
async def handle_message(update: Update, context):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота за ім'ям або юзернеймом, або якщо це особисте повідомлення
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message or update.message.chat.type == 'private':
        await update.message.reply_text('Генерую відповідь...')
        
        # Імітація написання
        await asyncio.sleep(random.uniform(1, 3))  # Імітація затримки
        response_text = await generate_response(message)
        
        if response_text:
            await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
        else:
            await update.message.reply_text('На жаль, сталася помилка при генерації відповіді.')

    # Втручання в розмову з ймовірністю 10%
    if random.random() < 0.1:
        await asyncio.sleep(random.uniform(1, 3))  # Імітація затримки
        random_message = "Це випадкова репліка від Дарини."  # Змінити на будь-який текст
        await update.message.reply_text(random_message)

    # Якщо хтось відповідає реплаєм на повідомлення бота
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        instruction_message = update.message.text
        await update.message.reply_text('Генерую відповідь на ваш запит...')
        
        # Імітація написання
        await asyncio.sleep(random.uniform(1, 3))  # Імітація затримки
        response_text = await generate_response(instruction_message)
        
        if response_text:
            await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
        else:
            await update.message.reply_text('На жаль, сталася помилка при генерації відповіді.')

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
