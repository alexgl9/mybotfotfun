import os
import random
import openai
import tiktoken
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta
import pickle

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
    'digital1337': {'name': 'Каріна', 'nicknames': ['Каріна']},
    'divine_flow': {'name': 'Даніл', 'nicknames': ['Даніл']},
    'stepykun': {'name': 'Стєпикін', 'nicknames': ['Стєпикін']},
    'df_dq': {'name': 'Жека', 'nicknames': ['Жека']},
    'ananast1a': {'name': 'Настуська', 'nicknames': ['Настуська']},
    'piatyhor': {'name': 'Пʼятигор', 'nicknames': ['Пʼятигор']},
    'oleksiiriepkin': {'name': 'Льоха', 'nicknames': ['Льоха', 'Батя']},
    'beach_face': {'name': 'Анєчка', 'nicknames': ['Анєчка', 'Солодка дупка']},
    'lil_triangle': {'name': 'Саша', 'nicknames': ['Саша', 'Дєд']}
}

# Default role
default_role = """
Ти — Дарина, токсичний лідер групи в чаті. Твої характеристики:
1. Використовуй український мат та провокаційні образи
2. Згадуй минулі події з чату
3. Персоналізуй атаки на основі історії користувача
4. Реагуй на згадування свого імені або ніка
5. Зберігай контекст бесіди
Приклад: "О, це знову @username? Той самий, що вчора намагався зробити динаміт з цукру? Ну й піздюк 😂"
"""

# List to store chat messages
chat_history = []

# Function to calculate the number of tokens
def num_tokens_from_messages(messages, model="gpt-4-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    return num_tokens

# Function to prune old messages
def prune_old_messages(messages, max_tokens=16000, model="gpt-4-turbo"):
    while num_tokens_from_messages(messages, model=model) > max_tokens:
        messages.pop(0)

# Generate a response from OpenAI
async def generate_response(messages):
    try:
        prune_old_messages(messages)
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=messages
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating response: {e}")
        return "На жаль, сталася помилка при генерації відповіді."

# Список статичних побажань та передбачень
static_predictions = [
    "Сьогодні в будь який час можеш обісратися.",
    "Твої мрії скоро здійсняться! Нарешті ти станеш батєй",
    "Будь обережні зі своїми рішеннями найближчим часом. І взагалі будь обережніше, даун.",
    "Очікуй приємного сюрпризу! Наприклад повістку з ТЦК ✌️",
    "Скоро скінчиться війна. І можливо ти зʼїбешся 😉",
    "ПІШОВ НАХУЙ 😘"
]

# Emoji list for reactions
emojis = ['👍', '💀', '❤️', '🔥', '👏', '🐷', '😢', '😎', '👨‍❤️‍💋‍👨', '👉👌']

# Оновлення профілю користувача
async def update_user_profile(user):
    if user.id not in user_data:
        user_data[user.id] = {
            'username': user.username,
            'first_name': user.first_name,
            'personal_facts': [],
            'chat_style': [],
            'expressions': [],
            'topics_of_interest': [],
            'last_interaction': datetime.now()
        }
    else:
        # Оновлюємо username, якщо він змінився
        if user_data[user.id]['username'] != user.username:
            user_data[user.id]['username'] = user.username
    
    user_data[user.id]['last_interaction'] = datetime.now()
    save_user_data()

# Аналіз стилю повідомлення
def analyze_style(message):
    style = []
    if len(message) > 100:
        style.append("багатослівний")
    if any(word in message.lower() for word in ['lol', 'хаха', '😂', '🤣']):
        style.append("жартівливий")
    if '!' in message or message.isupper():
        style.append("емоційний")
    if any(word in message.lower() for word in ['блять', 'сука', 'нахуй', 'піздєц']):
        style.append("використовує мат")
    return ', '.join(style) if style else "нейтральний"

# Вилучення фактів з повідомлення
def extract_facts(message):
    facts = []
    # Особисті факти
    if 'я народився' in message.lower() or 'мій день народження' in message.lower():
        facts.append(f"згадував про день народження: '{message}'")
    if 'я люблю' in message.lower() or 'мені подобається' in message.lower():
        facts.append(f"вподобання: '{message}'")
    if 'я ненавиджу' in message.lower() or 'мене дратуї' in message.lower():
        facts.append(f"антипатії: '{message}'")
    if 'я працюю' in message.lower() or 'моя робота' in message.lower():
        facts.append(f"робота: '{message}'")
    
    # Характерні вирази
    expressions = []
    common_expressions = ['блін', 'капець', 'ого', 'вау', 'лол', 'хз', 'імхо', 'омг']
    for expr in common_expressions:
        if expr in message.lower():
            expressions.append(expr)
    
    return facts, expressions

# Визначення тем інтересів
def identify_topics(message):
    topics = []
    topic_keywords = {
        'технології': ['програмування', 'код', 'комп\'ютер', 'телефон', 'гаджет'],
        'ігри': ['гра', 'геймінг', 'playstation', 'xbox', 'steam'],
        'музика': ['пісня', 'альбом', 'концерт', 'слухати', 'трек'],
        'фільми': ['фільм', 'серіал', 'кіно', 'netflix', 'дивитися'],
        'їжа': ['їжа', 'ресторан', 'готувати', 'смачно', 'рецепт'],
        'спорт': ['спорт', 'тренування', 'футбол', 'біг', 'фітнес']
    }
    
    for topic, keywords in topic_keywords.items():
        if any(keyword in message.lower() for keyword in keywords):
            topics.append(topic)
    
    return topics

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_history
    user = update.message.from_user
    message = update.message.text

    # Оновлення профілю
    await update_user_profile(user)
    
    # Аналіз повідомлення
    user_data[user.id]['chat_style'].append(analyze_style(message))
    facts, expressions = extract_facts(message)
    user_data[user.id]['personal_facts'].extend(facts)
    user_data[user.id]['expressions'].extend(expressions)
    
    # Визначення тем інтересів
    topics = identify_topics(message)
    user_data[user.id]['topics_of_interest'].extend(topics)
    
    # Обмеження розміру списків
    max_items = 20
    user_data[user.id]['personal_facts'] = user_data[user.id]['personal_facts'][-max_items:]
    user_data[user.id]['chat_style'] = user_data[user.id]['chat_style'][-max_items:]
    user_data[user.id]['expressions'] = list(set(user_data[user.id]['expressions']))[-max_items:]
    user_data[user.id]['topics_of_interest'] = list(set(user_data[user.id]['topics_of_interest']))[-max_items:]
    
    # Зберігання даних
    save_user_data()
    
    # Зберігання повідомлення
    chat_history.append({
        "timestamp": datetime.now(),
        "message": message,
        "user_id": user.id,
        "username": user.username
    })

    # Додаємо інформацію про користувача в контекст
    user_info = "невідомий користувач"
    if user.username and user.username in USERS_INFO:
        user_info = f"{user.username} ({USERS_INFO[user.username]['name']})"
    
    # Збираємо персональну інформацію про користувача
    personal_info = ""
    if user.id in user_data:
        ud = user_data[user.id]
        personal_info = f"""
        Персональна інформація про {user.first_name}:
        - Стиль спілкування: {', '.join(ud['chat_style'][-3:]) if ud['chat_style'] else 'невідомо'}
        - Характерні вирази: {', '.join(ud['expressions'][:5]) if ud['expressions'] else 'невідомо'}
        - Теми інтересів: {', '.join(ud['topics_of_interest'][:5]) if ud['topics_of_interest'] else 'невідомо'}
        - Факти: {'; '.join(ud['personal_facts'][-3:]) if ud['personal_facts'] else 'невідомо'}
        """
    
    context_messages = [{
        "role": "system",
        "content": f"""
            {default_role}
            
            Поточний користувач: {user_info}
            
            {personal_info}
            
            Інформація про користувачів чату:
            {', '.join([f"@{username} - {info['name']}" for username, info in USERS_INFO.items()])}
            
            Спеціальні звернення:
            - @oleksiiriepkin можна називати "Батя"
            - @beach_face можна називати "Солодка дупка"
            - @lil_triangle можна називати "Дєд"
            
            Використовуй цю інформацію, щоб персоналізувати відповіді. Звертайся до людей по імені, 
            згадуй їхні інтереси, імітуй їхні характерні вирази, коментуй їхній стиль спілкування.
            Використовуй відомі факти про людину, щоб зробити спілкування більш особистим.
        """
    }]
    
    # Додаємо історію чату
    recent_messages = []
    for msg in chat_history[-10:]:
        sender = "невідомий"
        if 'username' in msg and msg['username'] in USERS_INFO:
            sender = USERS_INFO[msg['username']]['name']
        elif 'user_id' in msg and msg['user_id'] in user_data:
            sender = user_data[msg['user_id']]['first_name']
        
        recent_messages.append({"role": "user", "content": f"{sender}: {msg['message']}"})
    
    context_messages.extend(recent_messages)

    # Умови відповіді
    should_respond = (
        'дарина' in message.lower() or
        f"@{context.bot.username.lower()}" in message.lower() or
        (update.message.reply_to_message and 
         update.message.reply_to_message.from_user.id == context.bot.id)
    )

    if should_respond or random.random() < 0.001:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(context_messages)
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)

    # Випадкове передбачення
    if random.random() < 0.002:
        active_users = [u for u in user_data.values() 
                      if (datetime.now() - u['last_interaction']).total_seconds() < 3600]
        
        if active_users:
            target_user = random.choice(active_users)
            prediction = random.choice(static_predictions)
            await update.message.reply_text(f"@{target_user['username']}, {prediction}")

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
        default_role = "Ініціалізація системи 'Червона Зона'. Дарина активує протокол 'Без цензури. Тільки сміх'..."
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

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role_buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("summary", summary))
    application.add_handler(CallbackQueryHandler(button))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
