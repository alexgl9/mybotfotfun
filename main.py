import os
import random
import asyncio
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Default role
default_role = "девчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки."

# Generate a response from OpenAI
async def generate_response(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are {default_role}."},
                {"role": "user", "content": message}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating response: {e}")
        return "На жаль, сталася помилка при генерації відповіді."

# Handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт! Я бот і відповідаю на твої питання.')

# Handle replies to bot messages
async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        # This is a reply to the bot's message
        message = update.message.text.lower()
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(message)
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)

# Handle regular messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.lower()

    # Check if the bot is mentioned by name or username
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(message)
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)

    # Randomly interject in the chat
    if random.random() < 0.1:  # 10% chance
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(message)
        await update.message.reply_text(response_text)

# Set a role for the bot
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global default_role
    if context.args:
        default_role = ' '.join(context.args)
        await update.message.reply_text(f"Роль змінено на: {default_role}")
    else:
        await update.message.reply_text("Будь ласка, надайте нову роль.")

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Reply(), handle_reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
