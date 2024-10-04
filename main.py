import os
import random
import asyncio
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Налаштування OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Стандартна роль
default_role = "Дівчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки."

# Змінна для зберігання ролі
current_role = default_role

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт! Я бот, якого звати Дарина. Я відповідаю на твої питання. Напиши /set, щоб змінити мою роль.')

# Обробник команди /set
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_role
    if context.args:
        new_role = ' '.join(context.args)
        current_role = new_role
        await update.message.reply_text(f'Роль змінено на: {new_role}')
    else:
        await update.message.reply_text('Будь ласка, введіть нову роль після команди /set.')

# Генерація відповіді від OpenAI
async def generate_response(message: str) -> str:
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful assistant with the role of {current_role}."},
                {"role": "user", "content": message}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating response: {e}")
        return "На жаль, сталася помилка при генерації відповіді."

# Обробник повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()

    # Перевірка, чи згадано бота за ім'ям або юзернеймом, або якщо це особисте повідомлення
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message or update.message.chat.type == 'private':
        typing_message = await update.message.reply_text('Генерую відповідь...')
        
        # Імітація часу набору
        await asyncio.sleep(random.uniform(1, 3))  # Час затримки від 1 до 3 секунд

        response_text = await generate_response(message)

        # Відповідь у вигляді реплаю
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_to_message_id=typing_message.message_id
        )

    # Випадкове втручання в бесіду
    if random.random() < 0.1:  # 10% ймовірності втручання
        random_reply = f"Цікаво, я б сказала: {random.choice(['Можливо, варто спробувати.', 'Це звучить цікаво!', 'Я б додала, що...'])}"
        await context.bot.send_message(update.effective_chat.id, random_reply)

# Обробник реплаїв на повідомлення бота
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Перевірка, чи є повідомлення реплаєм на повідомлення бота
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        message = update.message.text
        response_text = await generate_response(message)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text,
            reply_to_message_id=update.message.message_id
        )

async def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Скидання вебхука
    await application.bot.delete_webhook()

    # Додавання обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply))  # Видалено фільтр Reply()

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
