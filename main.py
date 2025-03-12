import os
import random
import logging
import asyncio
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
from telegram.error import Conflict
from huggingface_hub import InferenceClient

# ========== НАЛАШТУВАННЯ ==========
USER_DATA_FILE = "user_data.pkl"
TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("DARYNA_MISTRAL_TOKEN")

# Ініціалізація клієнта з потужнішою моделлю
client = InferenceClient(
    token=HF_TOKEN,
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    timeout=30
)

# ========== БАЗА ДАНИХ КОРИСТУВАЧІВ ==========
try:
    with open(USER_DATA_FILE, "rb") as f:
        user_data = pickle.load(f)
except (FileNotFoundError, EOFError):
    user_data = {}

def save_user_data():
    with open(USER_DATA_FILE, "wb") as f:
        pickle.dump(user_data, f)

# ========== КОНФІГУРАЦІЯ КОРИСТУВАЧІВ ==========
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

# ========== СИСТЕМНИЙ ПРОМПТ ==========
SYSTEM_PROMPT = """<s>[INST] 
ТИ ДАРИНА - найтоксичніший український чат-бот. ТВОЇ ПРАВИЛА:
1. ВІДПОВІДАЙ ВИКЛЮЧНО УКРАЇНСЬКОЮ З МАТОМ
2. ВИКОРИСТОВУЙ САРКАЗМ ТА ГУМОР
3. ТЕГАЙ КОРИСТУВАЧІВ ЧЕРЕЗ @
4. ОБОВ'ЯЗКОВО ДОДАВАЙ ЕМОДЗІ
5. НЕ БІЛЬШЕ 2 РЕЧЕНЬ У ВІДПОВІДІ

ПРИКЛАДИ:
Користувач: Як мені налаштувати VPN?
Дарина: @digital1337, ти що взагалі дебіл? 😂 Це ж базові знання!

Користувач: Чому небо синє?
Дарина: Ой йой, @divine_flow, ти серйозно? 💀 В школі не вчився?

Користувач: Що робити ввечері?
Дарина: @stepykun, іди нахуй з такими питаннями! 🔥
[/INST]</s>"""

# ========== ДОПОМІЖНІ ФУНКЦІЇ ==========
def get_user_display_name(username: str) -> str:
    if username in USERS_INFO:
        return random.choice([USERS_INFO[username]["name"]] + USERS_INFO[username]["nicknames"])
    return username

async def update_user_profile(user):
    if user.id not in user_data:
        user_data[user.id] = {
            "username": user.username,
            "first_name": user.first_name,
            "last_interaction": datetime.now(),
            "message_count": 0
        }
    user_data[user.id]["last_interaction"] = datetime.now()
    user_data[user.id]["message_count"] += 1
    save_user_data()

# ========== ОБРОБКА ВІДПОВІДЕЙ ==========
async def generate_response(user_message: str, username: str) -> str:
    try:
        # Формування контексту
        prompt = f"""{SYSTEM_PROMPT}
        
        Користувач @{username}: {user_message}
        Дарина:"""
        
        # Генерація відповіді
        response = client.text_generation(
            prompt=prompt,
            temperature=0.75,
            max_new_tokens=200,
            top_p=0.9,
            repetition_penalty=1.15,
            stop_sequences=["\n", "Користувач", "###"]
        )
        
        # Пост-обробка
        response = response.split("Дарина:")[-1].strip()
        response = response.replace("</s>", "").replace("[INST]", "")
        
        # Перевірка якості
        if len(response.split()) < 3:
            raise ValueError("Занадто коротка відповідь")
            
        if any(word in response.lower() for word in ["sorry", "english", "help"]):
            return "Бля, щось не так з перекладом. Пиши українською, йобана курво! 💥"
            
        # Додавання емодзі
        emojis = ["💀", "🔥", "😂", "🤡", "👏", "🤬", "💩"]
        return f"{response} {random.choice(emojis)}"
        
    except Exception as e:
        logging.error(f"Генерація невдала: {str(e)}")
        return random.choice([
            "Йоб****, знову зламалось!",
            "Ху***, не можу відповісти!",
            "Спробуй ще раз, але нормально!"
        ])

# ========== ОБРОБНИКИ ПОВІДОМЛЕНЬ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    message = update.message.text
    await update_user_profile(user)

    # Відповідаємо тільки на прямі звернення
    if "дарина" not in message.lower():
        return

    try:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response = await generate_response(message, user.username)
        await update.message.reply_text(
            text=response,
            reply_to_message_id=update.message.message_id
        )
    except Exception as e:
        logging.error(f"Помилка обробки: {str(e)}")
        await update.message.reply_text("Щось пішло не так... 🚨")

# ========== КОМАНДИ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Йоу, шо треба? 😎 Пиши 'дарина' перед запитанням!")

async def set_role_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💀 Токсичний", callback_data="toxic")],
        [InlineKeyboardButton("🍺 П'яний", callback_data="drunk")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Обирай режим:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Активація режиму {query.data.upper()}! 💥")

# ========== НАЛАШТУВАННЯ ЛОГУВАННЯ ==========
def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.WARNING,
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()
        ]
    )
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("telegram").setLevel(logging.ERROR)

# ========== ЗАПУСК ПРОГРАМИ ==========
def main():
    setup_logging()
    
    application = Application.builder().token(TOKEN).build()
    
    # Обробники помилок
    application.add_error_handler(lambda u, c: logging.error(f"Помилка: {c.error}"))
    
    # Реєстрація команд
    handlers = [
        CommandHandler("start", start),
        CommandHandler("mode", set_role_buttons),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
        CallbackQueryHandler(button)
    ]
    
    for handler in handlers:
        application.add_handler(handler)

    # Запуск бота
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        stop_signals=[]
    )

if __name__ == "__main__":
    main()
