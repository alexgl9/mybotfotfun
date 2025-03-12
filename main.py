import os
import random
import openai
import tiktoken
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta

# Налаштування API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Глобальні змінні
default_role = """
Ти - Дарина, токсичний лідер групи в чаті. Твої характеристики:
1. Використовуй український мат та провокаційні образи
2. Згадуй минулі події з чату
3. Персоналізуй атаки на основі історії користувача
4. Реагуй на згадування свого імені або ніка
5. Зберігай контекст бесіди
Приклад: "О, це знову @username? Той самий, що вчора намагався зробити динаміт з цукру? Ну й піздюк 😂"
"""

chat_history = []
user_context = {}
static_predictions = [...]  # Ваш список статичних побажань

# Утиліти для токенів
def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    encoding = tiktoken.encoding_for_model(model)
    return sum(len(encoding.encode(msg['content'])) for msg in messages)

def prune_old_messages(messages, max_tokens=14000):
    while num_tokens_from_messages(messages) > max_tokens:
        messages.pop(0)

# Генерація відповідей
async def generate_response(messages):
    try:
        prune_old_messages(messages)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Йобаний сервер знову вдавився! {random.choice(['Пішов нахуй!', 'Сам це роби!', 'Говно, а не API!'])}"

# Персоналізовані передбачення
async def generate_ai_prediction(user_id):
    user = user_context.get(user_id, {})
    try:
        return openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": f"""Створи жорстке передбачення для {user.get('name', 'йолк')}. 
                Використай ці теми: {', '.join(user.get('topics', ['тупість', 'нікчемність']))}.
                Стиль: {default_role}"""
            }]
        )
    except:
        return f"{random.choice(static_predictions} @{user.get('username', 'піздюк')}"

# Обробники Telegram
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_history
    user = update.message.from_user
    message = update.message.text
    
    # Оновлення контексту
    if user.id not in user_context:
        user_context[user.id] = {
            'username': user.username,
            'name': user.first_name,
            'topics': [],
            'last_active': datetime.now()
        }
    
    # Зберігання історії
    chat_history.append({
        'user_id': user.id,
        'text': message,
        'timestamp': datetime.now()
    })
    
    # Умови відповіді
    should_respond = (
        context.bot.username.lower() in message.lower() or 
        'дарина' in message.lower() or
        (update.message.reply_to_message and 
         update.message.reply_to_message.from_user.id == context.bot.id)
    )
    
    if should_respond or random.random() < 0.0005:
        context_msg = [
            {"role": "system", "content": f"""
            {default_role}
            Актуальний контекст:
            Учасники: {', '.join([f"{u['name']} (@{u['username']})" for u in user_context.values()])}
            Останні повідомлення: {', '.join([msg['text'][:20] for msg in chat_history[-3:]])}
            """},
            *[{"role": "user", "content": msg['text']} for msg in chat_history[-10:]]
        ]
        
        response = await generate_response(context_msg)
        await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

# Кнопки для зміни ролі
async def set_role_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Токсична сука", callback_data='toxic'), 
         InlineKeyboardButton("П'яна шльондра", callback_data='drunk')],
        [InlineKeyboardButton("Секс-бомба", callback_data='bomba')]
    ]
    await update.message.reply_text("Обирай мою нову роль:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    global default_role
    
    if query.data == 'toxic':
        default_role += " Агресивніше на 200%. Використовуй більше мату!"
    elif query.data == 'drunk':
        default_role += " Ти п'яна як чорт, всі твої відповіді через призму алкоголю!"
    elif query.data == 'bomba':
        default_role += " Твій головний інтерес - секс. Всі відповіді з еротичним підтекстом!"
    
    await query.edit_message_text(text=f"Нова роль активована! {random.choice(['Йди нахуй!', 'Чого ще?', 'Мені це подобається...'])}")

# Запуск бота
def main():
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    app.add_handler(CommandHandler('role', set_role_buttons))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    app.run_polling()

if __name__ == '__main__':
    main()
