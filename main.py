import os
import random
import asyncio
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Встановлюємо ключ OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Стандартна роль
default_role = "дівчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки."

# Генерація відповіді від OpenAI
async def generate_response(message, custom_id):
    try:
        # Підготовка запиту для пакетної обробки
        batch_input = [
            {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": f"You are {default_role}."},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 1000
                }
            }
        ]

        # Створення .jsonl файлу
        with open("batchinput.jsonl", "w") as f:
            for request in batch_input:
                f.write(f"{request}\n")

        # Завантаження файлу на OpenAI
        batch_input_file = openai.File.create(
            file=open("batchinput.jsonl", "rb"),
            purpose="batch"
        )

        # Створення пакету
        batch_response = openai.Batch.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": "Batch request for responses"}
        )

        # Перевірка статусу пакету
        batch_id = batch_response.id
        while True:
            batch_status = openai.Batch.retrieve(batch_id)
            if batch_status.status == "completed":
                break
            elif batch_status.status == "failed":
                return "На жаль, пакет не вдався."
            await asyncio.sleep(1)

        # Отримання результатів
        output_file_id = batch_status.output_file_id
        output = openai.File.content(output_file_id)
        # Повернення відповіді
        return output
    except Exception as e:
        print(f"Error generating response: {e}")
        return "На жаль, сталася помилка при генерації відповіді."

# Обробник команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт! Я бот і відповідаю на твої питання.')

# Обробник повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()

    # Перевіряємо, чи бот згаданий по імені або username
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(message, "request-1")
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)

    # Перевіряємо, чи це відповідь на повідомлення бота
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(message, "request-2")
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
        return

    # Випадкове втручання в чат
    if random.random() < 0.1:  # 10% ймовірність
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(message, "request-3")
        await update.message.reply_text(response_text)

# Зміна ролі бота через команду /set
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global default_role
    if context.args:
        default_role = ' '.join(context.args)
        await update.message.reply_text(f"Роль змінено на: {default_role}")
    else:
        await update.message.reply_text("Будь ласка, надайте нову роль.")

# Основна функція для запуску бота
def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
