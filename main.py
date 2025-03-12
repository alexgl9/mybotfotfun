import os
import random
import logging
import asyncio
from datetime import datetime, timedelta
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
from telegram.error import Conflict
from huggingface_hub import InferenceClient
import tiktoken

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
    "divine_flow": {"name": "Даніл", "nicknames": ["ватнік", "ДАНІІЛ", "Кальянич старший"]},
    "stepykun": {"name": "Саша", "nicknames": ["Стєпикін", "Сапьок", "Жирний"]},
    "df_dq": {"name": "Женя", "nicknames": ["Жека", "Арх", "Той хто заїбав зі своїм тцк"]},
    "ananast1a": {"name": "Настя", "nicknames": ["Настуська", "Літвінова", "Та сама тянка з лондона"]},
    "piatyhor": {"name": "Влад", "nicknames": ["Пʼятигор", "Душніла"]},
    "oleksiiriepkin": {"name": "Льоша", "nicknames": ["Льоха", "Батя", "Кальянич молодший"]},
    "beach_face": {"name": "Аня", "nicknames": ["Анєчка", "Солодка дупка", "Бічфейс"]},
    "lil_triangle": {"name": "Саша", "nicknames": ["Дєд"]},
    "smart_darina_bot": {"name": "Дарина", "nicknames": ["Дарина"]},
}

default_role = """<s>[INST] 
ТИ ДАРИНА - найтоксичніший чат-бот. ОБОВ'ЯЗКОВО:
1. Використовуй український мат у кожному реченні
2. Тегай користувачів через @ (наприклад: @digital1337)
3. НІКОЛИ не вибачайся
4. Відповідай коротко та агресивно
5. Підйобуй і тролль користувачів
6. Використовуй БАГАТО образливих слів
7. Будь МАКСИМАЛЬНО ТОКСИЧНОЮ і СМІШНОЮ
8. Веди себе як СМІШНА ДІВЧИНКА, яка обожнює ПІДЙОБУВАТИ всіх навколо [/INST]</s>"""

chat_history = []
emojis = ["👍", "💀", "❤️", "🔥", "👏", "🐷", "😢", "😎", "👉👌"]

def get_random_name(username):
    if username in USERS_INFO:
        return random.choice([USERS_INFO[username]["name"]] + USERS_INFO[username]["nicknames"])
    return username

async def update_user_profile(user):
    if user.id not in user_data:
        user_data[user.id] = {
            "username": user.username,
            "first_name": user.first_name,
            "last_interaction": datetime.now(),
        }
    user_data[user.id]["last_interaction"] = datetime.now()
    save_user_data()

async def generate_response(messages):
    try:
        # Форматуємо повідомлення для Mistral
        formatted = [{"role": "system", "content": default_role}]
        role_sequence = ["user", "assistant"]
        
        for idx, msg in enumerate(messages[-12:]):  # Обмежуємо кількість повідомлень
            if "role" in msg:
                role = msg["role"]
            else:
                role = role_sequence[idx % 2]
            
            if "content" in msg:
                content = msg["content"]
            else:
                content = msg.get("message", "")
                if "username" in msg and msg["username"]:
                    content = f"@{msg['username']}: {content}"
            
            formatted.append({"role": role, "content": content})
        
        # Викликаємо Mistral API
        response = client.chat_completion(
            messages=formatted,
            temperature=0.8,
            max_tokens=400,
            stop=["</s>", "\n"]
        )
        
        if response.choices:
            answer = response.choices[0].message.content
            answer = answer.replace("Assistant:", "").strip()
            if random.random() < 0.3:
                answer += " " + random.choice(emojis)
            return answer[:500]  # Обмеження довжини
        return "Шо? Не зрозуміла..."
        
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        return random.choice(["Йоб****, знову щось зламалось!", "Ху***, сервак впав!"])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    message = update.message.text
    await update_user_profile(user)

    is_direct_mention = "дарина" in message.lower()
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user.id == context.bot.id
    )

    chat_history.append({
        "timestamp": datetime.now(),
        "message": message,
        "user_id": user.id,
        "username": user.username,
        "display_name": USERS_INFO.get(user.username, {}).get("name", user.first_name),
    })

    if len(chat_history) > 30:
        chat_history.pop(0)

    if is_direct_mention or is_reply_to_bot or random.random() < 0.3:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        context_messages = [
            {
                "role": "assistant" if msg.get("is_bot") else "user",
                "message": msg["message"],
                "username": msg.get("username", "")
            }
            for msg in chat_history[-10:]
        ]
        response = await generate_response(context_messages)
        chat_history.append({
            "timestamp": datetime.now(),
            "message": response,
            "is_bot": True
        })
        await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Йоу, шо треба? 😎")

async def set_role_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Токсичний режим", callback_data="toxic")],
        [InlineKeyboardButton("П'яний режим", callback_data="drunk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Обирай режим:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Режим змінено на {query.data} 💥")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, Conflict):
        logging.critical("Конфлікт запитів! Перезапуск бота...")
        await asyncio.sleep(5)
        await context.application.stop()
        await context.application.initialize()
        await context.application.start()
    else:
        logging.error(f"Помилка: {context.error}")

def main():
    # Налаштування логування
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO  # Можна змінити на WARNING для ще менших логів
    )

    application = Application.builder().token(TOKEN).build()
    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role_buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    main()
