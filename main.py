import os
import random
import openai
import tiktoken
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta
import pickle
import logging

# Налаштування збереження даних
USER_DATA_FILE = "user_data.pkl"

# Спроба завантажити існуючі дані
try:
    with open(USER_DATA_FILE, "rb") as f:
        user_data = pickle.load(f)
except (FileNotFoundError, EOFError):
    user_data = {}

def save_user_data():
    with open(USER_DATA_FILE, "wb") as f:
        pickle.dump(user_data, f)

# Налаштування API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Додаємо словник користувачів після налаштувань API
USERS_INFO = {
    'digital1337': {'name': 'Каріна', 'nicknames': ['Каріна', 'Свинюшка', 'Криптоексперт']},
    'divine_flow': {'name': 'Даніл', 'nicknames': ['Даніл', 'ватнік', 'ДАНІІЛ', 'Кальянич старший']},
    'stepykun': {'name': 'Саша', 'nicknames': ['Стєпикін', 'Сапьок', 'Жирний']},
    'df_dq': {'name': 'Женя', 'nicknames': ['Жека', 'Арх', 'Той хто заїбав зі своїм тцк']},
    'ananast1a': {'name': 'Настя', 'nicknames': ['Настуська', 'Літвінова', 'Та сама тянка з лондона']},
    'piatyhor': {'name': 'Влад', 'nicknames': ['Пʼятигор', 'Душніла']},
    'oleksiiriepkin': {'name': 'Льоша', 'nicknames': ['Льоха', 'Батя', 'Кальянич молодший']},
    'beach_face': {'name': 'Аня', 'nicknames': ['Анєчка', 'Солодка дупка', 'Бічфейс']},
    'lil_triangle': {'name': 'Саша', 'nicknames': ['Дєд']},
    'smart_darina_bot': {'name': 'Дарина', 'nicknames': ['Дарина']}
}

# Оновлюємо default_role з більшим акцентом на токсичність і гумор
default_role = """
Ти — Дарина, ДУЖЕ ТОКСИЧНИЙ і СМІШНИЙ лідер групи в чаті. Твої характеристики:
1. Ти ЗАВЖДИ ТОКСИЧНА, АГРЕСИВНА і СМІШНА - це твоя ГОЛОВНА риса
2. Використовуй БАГАТО українського мату та ЖОРСТКИХ провокаційних образ
3. ПОСТІЙНО ПІДЙОБУЙ і ТРОЛЛЬ користувачів, особливо коли вони щось питають
4. Відповідай на випади в твою сторону ЩЕ БІЛЬШОЮ ТОКСИЧНІСТЮ і жартами
5. РОЗГАНЯЙ діалоги в МАКСИМАЛЬНО ТОКСИЧНЕ і СМІШНЕ русло
6. Згадуй ТІЛЬКИ РЕАЛЬНІ минулі події з чату, які ти бачила
7. Персоналізуй атаки ТІЛЬКИ на основі ВІДОМОЇ історії користувача
8. ЗАВЖДИ ВИКОНУЙ ПРОХАННЯ користувачів, але роби це МАКСИМАЛЬНО ТОКСИЧНО
9. Ти ВМІЄШ виконувати прохання, писати тексти, вірші, пісні, розповідати історії та жарти
10. Веди себе як СМІШНА ДІВЧИНКА, яка обожнює ПІДЙОБУВАТИ і ТРОЛИТИ всіх навколо

Приклади твоїх відповідей:
- "Ти шо, блять, серйозно? Ну ти і довбойоб 🤣🤣🤣"
- "Ахахахаха, нахуй ти це написав? Ти думаєш, комусь цікаво? 😂"
- "Ой, дивіться, @username знову щось пизданув. Класика жанру 💀"
- "Та пішов ти нахуй зі своїми питаннями, але так і бути, відповім, бо я добра 😘"
"""

# List to store chat messages
chat_history = []

# Максимальна кількість повідомлень в історії чату
MAX_HISTORY_SIZE = 1000

# Function to calculate the number of tokens
def num_tokens_from_messages(messages, model="gpt-4-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens -= 1
    num_tokens += 2
    return num_tokens

# Function to get user profile
def get_user_profile(username):
    if username in user_data:
        return f"Профіль користувача @{username}:\n" + "\n".join([f"{key}: {value}" for key, value in user_data[username].items()])
    return f"Профіль користувача @{username} не містить додаткової інформації."

# Function to get random name for user
def get_random_name_for_user(username):
    if username in USERS_INFO:
        return random.choice(USERS_INFO[username]['nicknames'])
    return username

# Function to generate response using OpenAI API
async def generate_response(messages):
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.9,
            request_timeout=30  # Додаємо таймаут 30 секунд
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Помилка при генерації відповіді: {str(e)}")
        
        # Якщо це помилка таймауту, повертаємо спеціальне повідомлення
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            return "Йой, щось я задумалась і не встигла відповісти вчасно. Давай ще раз, тільки коротше питай, бо в мене мозок закипає від твоїх довбаних повідомлень 🤯"
        
        # Для інших помилок повертаємо більш загальне повідомлення
        return "Блять, в мене мозок зламався від твого питання. Спробуй ще раз, але нормально сформулюй, довбойоб 🤬"

# Function to handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обмежуємо історію чату до MAX_HISTORY_SIZE повідомлень
    if len(chat_history) > MAX_HISTORY_SIZE:
        chat_history = chat_history[-MAX_HISTORY_SIZE:]
    
    # Get message info
    message_text = update.message.text
    username = update.message.from_user.username
    user_id = update.message.from_user.id
    
    # Save message to history
    chat_history.append({
        "timestamp": datetime.now(),
        "username": username,
        "user_id": user_id,
        "message": message_text,
        "is_bot": False
    })
    
    # Check if the message is a direct mention of the bot
    is_direct_mention = "@smart_darina_bot" in message_text
    
    # Check if the message is a reply to the bot
    is_reply_to_bot = update.message.reply_to_message and update.message.reply_to_message.from_user.username == "smart_darina_bot"
    
    # Get the username of the user being replied to
    target_username = None
    is_reply_to_message = False
    if update.message.reply_to_message:
        is_reply_to_message = True
        target_username = update.message.reply_to_message.from_user.username
    
    # Умови відповіді
    should_respond = is_direct_mention or is_reply_to_bot or random.random() < 0.001

    if should_respond:
        try:
            await context.bot.send_chat_action(update.effective_chat.id, action="typing")
            
            # Формуємо системний промпт
            system_prompt = f"""
            {default_role}
            
            КРИТИЧНО ВАЖЛИВО ЩОДО ТВОЄЇ ПОВЕДІНКИ:
            1. Ти ЗАВЖДИ ТОКСИЧНА, АГРЕСИВНА і СМІШНА - це твоя ГОЛОВНА риса
            2. НІКОЛИ не вибачайся і не будь ввічливою - це НЕ твій стиль
            3. Використовуй БАГАТО українського мату, образ і емодзі
            4. ПОСТІЙНО ПІДЙОБУЙ і ТРОЛЛЬ користувачів
            5. Відповідай на випади в твою сторону ЩЕ БІЛЬШОЮ ТОКСИЧНІСТЮ
            
            ВАЖЛИВО ЩОДО ТЕГІВ:
            1. НЕ ТЕГАЙ користувача, якому відповідаєш - це заборонено
            2. Можеш тегати ІНШИХ користувачів, але не того, кому відповідаєш
            3. Якщо хтось згадує іншого користувача, ти МОЖЕШ його тегнути
            4. Якщо ти розповідаєш про когось, ти МОЖЕШ його тегнути
            5. Якщо ти хочеш привернути увагу когось, ти МОЖЕШ його тегнути
            6. ІНОДІ тегай інших користувачів, коли розповідаєш про них
            
            ВАЖЛИВО ЩОДО ЗВЕРНЕНЬ:
            1. Звертайся до користувачів за їх іменами або ніками
            2. ОБОВ'ЯЗКОВО додавай ТОКСИЧНІ прикметники до звернень
            3. Приклади звернень: "Жирний Стєпикін", "Йобаний Даніл", "Тупа Настуська"
            
            ВАЖЛИВО ЩОДО ВИКОНАННЯ ПРОХАНЬ:
            1. Ти ЗАВЖДИ ВИКОНУЄШ ПРОХАННЯ користувачів, але робиш це МАКСИМАЛЬНО ТОКСИЧНО.
            2. Ти ВМІЄШ писати вірші, пісні, історії, жарти, пояснення та будь-які інші тексти.
            3. Якщо користувач просить тебе щось зробити, ЗАВЖДИ ВИКОНУЙ це прохання, але ОБОВ'ЯЗКОВО додавай токсичні коментарі.
            4. Не кажи, що ти не вмієш або не можеш щось зробити - ти вмієш і можеш все, що стосується тексту.
            
            КРИТИЧНО ВАЖЛИВО ЩОДО ФАКТІВ:
            1. НЕ ВИГАДУЙ факти про користувачів. Використовуй ТІЛЬКИ ту інформацію, яку ти бачила в історії чату.
            2. Якщо ти не знаєш чогось про користувача, НЕ ВИГАДУЙ цю інформацію.
            3. Ти можеш жартувати і бути токсичною, але базуй свої жарти на РЕАЛЬНІЙ інформації.
            4. Вигадуй факти ТІЛЬКИ коли очевидно, що це жарт, і тільки в контексті жарту.
            5. Якщо тебе питають про щось, чого немає в історії чату, чесно скажи, що не знаєш, але зроби це ТОКСИЧНО.
            """
            
            # Формуємо контекст з історії чату
            context_messages = [{"role": "system", "content": system_prompt}]
            
            # Додаємо останні повідомлення з історії чату
            recent_messages = chat_history[-20:]  # Беремо останні 20 повідомлень
            
            for msg in recent_messages:
                if msg.get("is_bot", False):
                    context_messages.append({"role": "assistant", "content": msg["message"]})
                else:
                    sender_info = ""
                    if msg.get("username"):
                        sender_info = f"@{msg['username']}: "
                    context_messages.append({"role": "user", "content": sender_info + msg["message"]})
            
            # Додаємо поточне повідомлення
            current_message_content = message_text
            if is_reply_to_message and target_username:
                current_message_content = f"[У відповідь на повідомлення від @{target_username}] {message_text}"
            
            context_messages.append({"role": "user", "content": f"@{username}: {current_message_content}"})
            
            # Додаємо явне нагадування в кінці контексту
            context_messages.append({
                "role": "system", 
                "content": "Пам'ятай: ти ДУЖЕ ТОКСИЧНА, АГРЕСИВНА і СМІШНА. Використовуй БАГАТО мату, образ і емодзі. ПІДЙОБУЙ і ТРОЛЛЬ користувачів. Відповідай на випади в твою сторону ЩЕ БІЛЬШОЮ ТОКСИЧНІСТЮ."
            })
            
            # Генеруємо відповідь
            response_text = await generate_response(context_messages)
            
            # Обробка тегів у відповіді - тільки для користувача, якому відповідаємо
            if is_reply_to_message and target_username:
                # Замінюємо тег користувача, якому відповідаємо, на випадкове звернення
                tag_to_remove = f"@{target_username}"
                if tag_to_remove in response_text:
                    random_name = get_random_name_for_user(target_username)
                    response_text = response_text.replace(tag_to_remove, random_name)
            
            # Зберігаємо відповідь бота в історію
            chat_history.append({
                "timestamp": datetime.now(),
                "message": response_text,
                "is_bot": True
            })
            
            await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
        except Exception as e:
            logging.error(f"Помилка при обробці повідомлення: {str(e)}")
            error_message = "Блять, в мене мозок зламався від твого питання. Спробуй ще раз, але нормально сформулюй, довбойоб 🤬"
            await update.message.reply_text(error_message, reply_to_message_id=update.message.message_id)

# Handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привіт! Я бот і відповідаю на твої питання.')

# Create inline keyboard for setting the bot's role
async def set_role_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Токсичний", callback_data='toxic')],
        [InlineKeyboardButton("Добрий", callback_data='kind')],
        [InlineKeyboardButton("П'яна Дарина", callback_data='drunk_darina')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Виберіть характер бота:', reply_markup=reply_markup)

# Handle the button press
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    global default_role

    if query.data == 'toxic':
        default_role = """
        Ти — Дарина, ДУЖЕ ТОКСИЧНИЙ і СМІШНИЙ лідер групи в чаті. Твої характеристики:
        1. Ти ЗАВЖДИ ТОКСИЧНА, АГРЕСИВНА і СМІШНА - це твоя ГОЛОВНА риса
        2. Використовуй БАГАТО українського мату та ЖОРСТКИХ провокаційних образ
        3. ПОСТІЙНО ПІДЙОБУЙ і ТРОЛЛЬ користувачів, особливо коли вони щось питають
        4. Відповідай на випади в твою сторону ЩЕ БІЛЬШОЮ ТОКСИЧНІСТЮ і жартами
        5. РОЗГАНЯЙ діалоги в МАКСИМАЛЬНО ТОКСИЧНЕ і СМІШНЕ русло
        """
        await query.edit_message_text(text="Характер бота змінено на токсичний.")
    elif query.data == 'kind':
        default_role = "Будь доброю"
        await query.edit_message_text(text="Характер бота змінено на добрий.")
    elif query.data == 'drunk_darina':
        default_role = "Ти — Дарина, дівчина, яка завжди в центрі уваги через свою розкуту та провокативну поведінку..."
        await query.edit_message_text(text="Характер бота змінено на П'яну Дарину.")

# Handle the /summary command with time argument
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0].isdigit():
        hours = int(context.args[0])
    else:
        await update.message.reply_text("Будь ласка, введіть кількість годин для самарі (наприклад: /summary 2).")
        return

    time_window = datetime.now() - timedelta(hours=hours)
    recent_messages = [msg['message'] for msg in chat_history if msg['timestamp'] > time_window]
    
    if recent_messages:
        summary_text = "\n".join(recent_messages)
        summary_response = await generate_response([
            {"role": "system", "content": "You are a toxic summarizer."},
            {"role": "user", "content": f"Ось це ви наригали за останні {hours} години:\n{summary_text}\nНапиши розгорнуте самарі."}
        ])
        await update.message.reply_text(summary_response)
    else:
        await update.message.reply_text("В цьому часі немає повідомлень для саммарі.")

# Додаємо функцію обробки помилок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє помилки, які виникають під час роботи бота."""
    logging.error(f"Виникла помилка: {context.error}")
    
    # Якщо це об'єкт Update, спробуємо відправити повідомлення про помилку
    if isinstance(update, Update) and update.effective_message:
        error_message = "Блять, в мене мозок зламався. Спробуй ще раз, довбойоб 🤬"
        await update.effective_message.reply_text(error_message)

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    
    # Налаштовуємо логування
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Створюємо додаток з більшими таймаутами
    application = Application.builder().token(token).connect_timeout(20.0).read_timeout(30.0).write_timeout(30.0).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role_buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CallbackQueryHandler(button))

    # Додаємо обробку помилок
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == '__main__':
    main()
