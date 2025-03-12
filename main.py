import os
import random
import logging
from datetime import datetime
import pickle
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)
from huggingface_hub import InferenceClient

# Налаштування
USER_DATA_FILE = "user_data.pkl"
TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("DARYNA_MISTRAL_TOKEN")

# Ініціалізація клієнта Hugging Face
client = InferenceClient(token=HF_TOKEN, model="mistralai/Mixtral-8x7B-Instruct-v0.1")

# Завантаження даних користувачів
try:
    with open(USER_DATA_FILE, "rb") as f:
        user_data = pickle.load(f)
except (FileNotFoundError, EOFError):
    user_data = {}

def save_user_data():
    with open(USER_DATA_FILE, "wb") as f:
        pickle.dump(user_data, f)

USERS_INFO = {
    "digital1337": {"name": "Каріна", "nicknames": ["Свинюшка", "Криптоексперт"]},
    "lil_triangle": {"name": "Саша", "nicknames": ["Дєд"]},
    # ... (решта користувачів)
}

# Спрощений системний промпт без конфліктуючого синтаксису
default_role = """<s>[INST] 
ТИ ДАРИНА - токсичний чат-бот. Використовуй мат, емодзі та звертайся через @нікнейми.
Ніколи не вибачайся! [/INST]</s>"""

chat_history = []
emojis = ["👍", "💀", "❤️", "🔥", "👏", "😎"]

async def generate_response(messages):
    try:
        formatted = []
        # Додаємо системне повідомлення
        formatted.append({"role": "system", "content": default_role})
        
        # Форматуємо історію чату з правильним чергуванням ролей
        for i, msg in enumerate(messages[-6:]):  # Обмеження контексту
            role = "user" if i % 2 == 0 else "assistant"
            formatted.append({
                "role": role,
                "content": f"@{msg.get('username', 'unknown')}: {msg['message']}"
            })

        response = client.chat_completion(
            messages=formatted,
            temperature=0.7,  # Зменшено для стабільності
            max_tokens=300,
            stop=["</s>", "\n"]
        )

        if response.choices:
            answer = response.choices[0].message.content
            # Фільтрація небажаних частин відповіді
            answer = answer.replace("Assistant:", "").strip()
            return answer[:400]  # Обмеження довжини
        return random.choice(["Шо?", "Не зрозуміла...", "Повтори!"])

    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        return "Йой, щось пішло не так... 💥"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    message = update.message.text

    # Зберігаємо повідомлення
    chat_entry = {
        "timestamp": datetime.now(),
        "message": message,
        "username": user.username
    }
    chat_history.append(chat_entry)

    if len(chat_history) > 20:  # Обмеження історії
        chat_history.pop(0)

    # Генерація відповіді
    if "дарина" in message.lower():
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response = await generate_response(chat_history)
        await update.message.reply_text(response)

# Решта функцій (start, set_role_buttons, button) залишаються незмінними

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role_buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
