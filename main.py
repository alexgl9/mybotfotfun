import os
import telebot
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(func=lambda message: True)
def respond(message):
    logging.info(f"Received message: {message.text}")  # Логування отриманого повідомлення
    if "Олєг" in message.text:
        bot.reply_to(message, "Привіт! Як я можу допомогти?")
    else:
        bot.reply_to(message, "Я тут!")

if __name__ == "__main__":
    logging.info("Bot is polling...")  # Логування запуску бота
    bot.polling()
