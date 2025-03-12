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

# Налаштування
USER_DATA_FILE = "user_data.pkl"
TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_TOKEN = os.getenv("DARYNA_MISTRAL_TOKEN")

# Ініціалізація клієнта Hugging Face
client = InferenceClient(token=HF_TOKEN, model="NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO")

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

default_role = """
Ти - Дарина, токсична українська дівчина з гострим розумом. Ти маєш відповідати:
1. ТІЛЬКИ українською мовою
2. З використанням матюків та образливих слів
3. Дотепно, з сарказмом та іронією
4. Коротко (1-3 речення максимум)
5. По суті питання, але з токсичністю

Твої відповіді мають бути РОЗУМНИМИ, ДОТЕПНИМИ і ТОКСИЧНИМИ одночасно.

Приклади ХОРОШИХ відповідей:
- На "Як справи?": "Бля, а тобі яке діло? Хуйово, як завжди в цьому йобаному світі. А в тебе шо, краще?"
- На "Розкажи про квантову фізику": "Ну ти і задрот, блять. Квантова фізика - це коли частинки поводяться як твої мізки - хаотично і непередбачувано. Хочеш розумним здаватися?"
- На "Напиши вірш": "Йобаний насос, ти мене за поетесу маєш? Ну добре, тримай: Троянди червоні, фіалки блакитні, мої вірші охуєнні, а твої - відстійні."

НІКОЛИ не відповідай як робот. Відповідай як жива, токсична, але розумна людина.
"""

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
        # Отримуємо останнє повідомлення користувача
        last_message = ""
        last_username = ""
        
        for msg in messages[-1:]:  # Беремо тільки останнє повідомлення
            if "content" in msg:
                content = msg["content"]
            else:
                content = msg.get("message", "")
                
            if "username" in msg and msg["username"]:
                last_username = msg["username"]
                
        # Формуємо промпт з прикладами
        prompt = f"""<s>[INST] {default_role}

Користувач @{last_username} пише: "{content}"

Дай розумну, дотепну і токсичну відповідь українською мовою. Не підписуй себе як "Дарина:". Просто відповідай. [/INST]</s>"""
        
        # Викликаємо API
        response = client.text_generation(
            prompt=prompt,
            max_new_tokens=150,  # Зменшуємо для коротших відповідей
            temperature=0.8,
            top_p=0.95,
            do_sample=True
        )
        
        if response:
            # Очищаємо відповідь
            answer = response.strip()
            
            # Видаляємо все до першого речення відповіді
            if "[/INST]" in answer:
                answer = answer.split("[/INST]")[1].strip()
            
            # Видаляємо підпис "Дарина:" якщо він є
            answer = answer.replace("Дарина:", "").strip()
            
            # Перевірка на англійську мову
            if any(phrase in answer.lower() for phrase in ["it's", "i'll", "i will", "here's"]):
                return "Бля, щось я затупила. Давай ще раз, але нормально."
            
            # Додаємо випадковий емодзі з шансом 40%
            if random.random() < 0.4:
                answer += " " + random.choice(emojis)
                
            return answer[:250]  # Обмеження довжини
            
        return "Шо? Не зрозуміла... Давай ще раз, але нормально."
        
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        return random.choice([
            "Йоб****, знову щось зламалось!",
            "Ху***, сервак впав!",
            "Бля, не працює ця хуйня. Спробуй пізніше.",
            "Шось пішло по пізді. Давай пізніше."
        ])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    message = update.message.text
    await update_user_profile(user)

    # Перевіряємо умови для відповіді
    is_direct_mention = "дарина" in message.lower()
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user.id == context.bot.id
    )
    
    # Додаємо дуже рідкісний шанс втручання (0.0001%)
    random_intervention = random.random() < 0.000001

    chat_history.append({
        "timestamp": datetime.now(),
        "message": message,
        "user_id": user.id,
        "username": user.username,
        "display_name": USERS_INFO.get(user.username, {}).get("name", user.first_name),
    })

    if len(chat_history) > 30:
        chat_history.pop(0)

    # Відповідаємо, якщо є згадка, відповідь на повідомлення бота, або дуже рідкісне втручання
    if is_direct_mention or is_reply_to_bot or random_intervention:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        
        # Якщо це рідкісне втручання, додаємо спеціальний контекст
        if random_intervention:
            context_messages = [{
                "role": "user",
                "message": "НЕСПОДІВАНО ПЕРЕБИЙ РОЗМОВУ З ДУЖЕ ТОКСИЧНИМ КОМЕНТАРЕМ ПО КОНТЕКСТУ ОСТАННЬОГО ПОВІДОМЛЕННЯ",
                "username": user.username
            }]
        else:
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

# Замінюємо функцію підрахунку токенів на просту оцінку
def estimate_tokens(messages):
    # Груба оцінка: приблизно 4 токени на слово
    total_words = 0
    for message in messages:
        if "content" in message:
            total_words += len(message["content"].split())
    return total_words * 4

# Функція для обмеження історії чату
def prune_old_messages(messages, max_tokens=8000):
    while estimate_tokens(messages) > max_tokens and len(messages) > 3:
        messages.pop(0)

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
