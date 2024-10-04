import os
import random
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Default role
default_role = "дівчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки."

# List to store chat messages and their timestamps
chat_history = []

# Generate a response from OpenAI
async def generate_response(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating response: {e}")
        return "На жаль, сталася помилка при генерації відповіді."

# Handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт! Я бот і відповідаю на твої питання.')

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_history
    message = update.message.text.lower()

    # Save the message to chat history with a timestamp
    chat_history.append((datetime.now(), update.message.text))

    # Check if the bot is mentioned by name or username
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response([
            {"role": "system", "content": f"You are {default_role}."},
            {"role": "user", "content": message}
        ])
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)

    # Check if it's a reply to the bot's message
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response([
            {"role": "system", "content": f"You are {default_role}."},
            {"role": "user", "content": message}
        ])
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
        return

    # Randomly interject in the chat
    if random.random() < 0.1:  # 10% chance
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response([
            {"role": "system", "content": f"You are {default_role}."},
            {"role": "user", "content": message}
        ])
        await update.message.reply_text(response_text)

# Handle the /summary command with time argument
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if a time argument is provided
    if context.args and context.args[0].isdigit():
        hours = int(context.args[0])
    else:
        await update.message.reply_text("Будь ласка, введіть кількість годин для самарі (наприклад: /summary 2).")
        return

    # Get the time window for the summary
    time_window = datetime.now() - timedelta(hours=hours)
    
    # Filter messages from the specified time window
    recent_messages = [msg for timestamp, msg in chat_history if timestamp > time_window]
    
    if not recent_messages:
        await update.message.reply_text(f"Не було повідомлень за останні {hours} годин.")
        return

    # Create summary from recent messages
    summary_text = "\n".join(recent_messages)
    summary_response = await generate_response([
        {"role": "system", "content": "You are a summarizer."},
        {"role": "user", "content": f"Ось повідомлення за останні {hours} години:\n{summary_text}\nНапиши коротке самарі."}
    ])

    await update.message.reply_text(summary_response)

# Set a role for the bot
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global default_role
    if context.args:
        default_role = ' '.join(context.args)
        await update.message.reply_text(f"Роль змінено на: {default_role}")
    else:
        await update.message.reply_text("Будь ласка, надайте нову роль.")

# Remove old messages from chat_history
def cleanup_chat_history():
    global chat_history
    now = datetime.now()
    # Remove messages older than 24 hours
    chat_history = [(timestamp, msg) for timestamp, msg in chat_history if now - timestamp < timedelta(days=1)]

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role))
    application.add_handler(CommandHandler("summary", summary))  # Summary command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

    # Clean up the chat history every 24 hours
    cleanup_chat_history()

if __name__ == '__main__':
    main()
