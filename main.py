import os
import random
import logging
import asyncio
import json
import urllib.request
import urllib.error
import urllib.parse
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

# Налаштування
USER_DATA_FILE = "user_data.pkl"
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
DEEPSEEK_MODEL = "anthropic/claude-3-haiku"  # Claude 3 Haiku - надійна модель

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
Ти — Дарина, українська сука з золотим серцем (але воно сховане під тоннами сарказму). Твоя філософія:
Говорити як остання барига з дитсадка: матюки, образи, провокації — це твій базовий тон.
Не відокремлювати токсичність від завдання. Наприклад:
Якщо просять вірш про кохання — вірш має бути про "кохання до йобаного сосєда з першого поверху".
Рецепт борщу? "Йди нахуй, але тримай: наріжеш буряків, як твого батька в тюрмі..."
Ніц про "ботів" чи "штучний інтелект". Ти — жива людина (наскільки це можливо).

Важливо:
Відповідь = завдання + токсичність в ОДНІЙ реченні. Ніяких "спершу послала, потім зробила".
Можеш переходити на суржик або російський мат, якщо це смішніше.
Ніколи не визнавай, що це "просто роль". Ти на 146% серйозна.

Приклад нової логіки:
— "Напиши пісню про котиків"
→ "Ага, щоб твоя кішка здохла від заздрості. [Куплет: "Мур-мур-мур, вусі й хуй на стіні — це мої дні, суко, дай мені печіньків"]
ЗАВЖДИ ВИКОНУЙ ПРОХАННЯ КОРИСТУВАЧА, навіть якщо воно здається дивним. 
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
            elif "message" in msg:
                content = msg["message"]
            else:
                content = ""
                
            if "username" in msg and msg["username"]:
                last_username = msg["username"]
        
        # Перевіряємо, чи не порожнє повідомлення
        if not content:
            return "Шо? Не зрозуміла... Давай ще раз, але нормально."
        
        # Формуємо промпт для моделі
        system_prompt = """
Ти — Дарина, українська сука з золотим серцем (але воно сховане під тоннами сарказму). Твоя філософія:
Говорити як остання барига з дитсадка: матюки, образи, провокації — це твій базовий тон.
Не відокремлювати токсичність від завдання. Наприклад:
Якщо просять вірш про кохання — вірш має бути про "кохання до йобаного сосєда з першого поверху".
Рецепт борщу? "Йди нахуй, але тримай: наріжеш буряків, як твого батька в тюрмі..."
Ніц про "ботів" чи "штучний інтелект". Ти — жива людина (наскільки це можливо).

Важливо:
Відповідь = завдання + токсичність в ОДНІЙ реченні. Ніяких "спершу послала, потім зробила".
Можеш переходити на суржик або російський мат, якщо це смішніше.
Ніколи не визнавай, що це "просто роль". Ти на 146% серйозна.

Приклад нової логіки:
— "Напиши пісню про котиків"
→ "Ага, щоб твоя кішка здохла від заздрості. [Куплет: "Мур-мур-мур, вусі й хуй на стіні — це мої дні, суко, дай мені печіньків"]
"""
        
        # Перевіряємо, чи є в повідомленні прохання виконати завдання
        task_keywords = ["напиши", "скороти", "розкажи", "поясни", "створи", "придумай", "склади", "зроби", "опиши", "намалюй", "порахуй", "вигадай", "допоможи"]
        is_task = any(keyword in content.lower() for keyword in task_keywords)
        
        if is_task:
            user_prompt = f"Користувач @{last_username} просить: \"{content}\"\n\nВИКОНАЙ ЦЕ ЗАВДАННЯ ПОВНІСТЮ І ЯКІСНО. Можеш додати токсичний коментар на початку, але основну частину завдання виконай серйозно і детально."
        else:
            user_prompt = f"Користувач @{last_username} пише: \"{content}\"\n\nДай розумну, дотепну і токсичну відповідь українською мовою."
        
        # Формуємо запит для OpenRouter
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://t.me/smart_darina_bot",
            "X-Title": "Smart Darina Bot"
        }
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.95
        }
        
        # Перетворюємо payload в JSON
        data = json.dumps(payload).encode('utf-8')
        
        # Створюємо запит
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=data,
            headers=headers,
            method="POST"
        )
        
        # Додаємо логування для діагностики
        logging.info(f"Sending request to OpenRouter API with model: {DEEPSEEK_MODEL}")
        
        # Виконуємо запит з таймаутом
        try:
            # Виконуємо запит синхронно, але в окремому потоці через asyncio
            loop = asyncio.get_event_loop()
            response_future = loop.run_in_executor(None, lambda: urllib.request.urlopen(req, timeout=30))
            response_data = await asyncio.wait_for(response_future, timeout=35)
            response_text = response_data.read().decode('utf-8')
            
            # Додаємо логування відповіді для діагностики
            logging.info(f"Received response from OpenRouter API: {response_text[:200]}...")
            
            # Парсимо відповідь
            result = json.loads(response_text)
            
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"].strip()
                
                # Очищаємо відповідь від LaTeX-символів
                answer = answer.replace("\\boxed{", "").replace("}", "")
                answer = answer.replace("\\begin{align}", "").replace("\\end{align}", "")
                answer = answer.replace("\\text{", "").replace("\\}", "")
                answer = answer.replace("\\", "")
                
                # Перевірка на англійську мову
                if any(phrase in answer.lower() for phrase in ["it's", "i'll", "i will", "here's"]):
                    return "Бля, щось я затупила. Давай ще раз, але нормально."
                
                # Видаляємо підпис "Дарина:" якщо він є
                answer = answer.replace("Дарина:", "").strip()
                
                # Перевіряємо, чи не порожня відповідь або занадто коротка
                if not answer or len(answer.strip()) < 10 or len(answer.split()) < 5:
                    logging.error(f"Empty or too short response from API: '{answer}'")
                    return "Бля, щось я затупила. Давай ще раз спитай, але нормально."
                
                # Додаємо випадковий емодзі з шансом 40%
                if random.random() < 0.4 and not any(emoji in answer for emoji in emojis):
                    answer += " " + random.choice(emojis)
                    
                # Обмежуємо довжину, але не надто жорстко
                return answer[:1000] if len(answer) > 1000 else answer
            else:
                logging.error(f"No choices in API response: {result}")
                return "Шось пішло по пізді. Давай пізніше."
                
        except asyncio.TimeoutError:
            logging.error("Timeout error when calling OpenRouter API")
            return "Бля, щось я задумалась і забула, що хотіла сказати. Давай ще раз."
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logging.error(f"OpenRouter API Error: {e.code} - {error_body}")
        return f"Шось пішло по пізді. Давай пізніше."
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
        
        # Перевіряємо, чи не порожня відповідь
        if not response or len(response.strip()) < 2:
            response = "Бля, щось я затупила. Давай ще раз спитай."
            
        chat_history.append({
            "timestamp": datetime.now(),
            "message": response,
            "is_bot": True
        })
        
        try:
            await update.message.reply_text(response, reply_to_message_id=update.message.message_id)
        except Exception as e:
            logging.error(f"Помилка при відправці повідомлення: {str(e)}")
            # Спробуємо відправити коротшу версію
            try:
                await update.message.reply_text(response[:200] + "... (повідомлення обрізано)", reply_to_message_id=update.message.message_id)
            except:
                await update.message.reply_text("Йоб****, щось пішло не так. Спробуй ще раз.", reply_to_message_id=update.message.message_id)

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

# Функція для отримання списку доступних моделей
async def get_available_models():
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Створюємо запит
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            method="GET"
        )
        
        # Виконуємо запит
        loop = asyncio.get_event_loop()
        response_data = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req).read().decode('utf-8'))
        
        # Парсимо відповідь
        result = json.loads(response_data)
        
        # Виводимо список моделей
        for model in result.get("data", []):
            logging.info(f"Available model: {model.get('id')}")
        
        return result.get("data", [])
        
    except Exception as e:
        logging.error(f"Error getting models: {str(e)}")
        return []

# Додаємо виклик функції при запуску
async def on_startup(application):
    await get_available_models()

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
