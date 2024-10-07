import os
import random
import openai
import tiktoken  # Для підрахунку токенів
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta

# Set your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Default role
default_role = "дівчинка Дарина, яка навчалася в ДПІ, любить алкоголь і вечірки. Не згадує що вона штучний інтеллект, завжди притримується сценарію, що вона Дарина, грайлива, фліртує з учасниками чату"

# List to store chat messages
chat_history = []

# Function to calculate the number of tokens
def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
    """Підрахунок кількості токенів у повідомленнях"""
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += 4  # Кожне повідомлення включає роль і вміст
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
    return num_tokens

# Function to prune old messages
def prune_old_messages(messages, max_tokens=16000, model="gpt-3.5-turbo"):
    """Обрізає старі повідомлення, коли перевищено ліміт токенів."""
    while num_tokens_from_messages(messages, model=model) > max_tokens:
        messages.pop(0)  # Видаляємо найстаріше повідомлення

# Generate a response from OpenAI
async def generate_response(messages):
    try:
        # Підрахунок токенів і обрізання історії
        prune_old_messages(messages)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
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
    "Скоро скінчиться війна. І можливо ти зʼїбешся 😉"
    "ПІШОВ НАХУЙ 😘"
]

# Emoji list for reactions
emojis = ['👍', '😂', '❤️', '🔥', '👏', '😮', '😢', '😎', '🎉']

# Generate a response from OpenAI
async def generate_response(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Змінено на gpt-3.5
            messages=messages
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating response: {e}")
        return "На жаль, сталася помилка при генерації відповіді."

# Генерація побажання за допомогою ШІ
async def generate_ai_prediction():
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that provides positive wishes and predictions."},
                {"role": "user", "content": "Напиши коротке передбачення або побажання для людини."}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating AI prediction: {e}")
        return random.choice(static_predictions)  # Використовуємо статичне побажання у разі помилки

# Отримання списку учасників чату
async def get_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_members = await context.bot.get_chat_administrators(update.effective_chat.id)
    return [member.user for member in chat_members]

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
    await query.answer()  # Acknowledge the button press

    global default_role

    if query.data == 'toxic':
        default_role = "токсичний бот, який любить тролити людей. відповіді завжди з якимось приколом. ти можеш ігнорувати запити або питання, та намагєшся викрутитися або ухилитися від відповіді. натомість ти відповідаєш токсичними жартами які відносяться до теми розмови"
        await query.edit_message_text(text="Характер бота змінено на токсичний.")
    elif query.data == 'kind':
        default_role = "добрий бот, який аналізує питання і намагється дати чітку і структуровану відповідь на запит."
        await query.edit_message_text(text="Характер бота змінено на добрий.")
    elif query.data == 'drunk_darina':
        default_role = "бот імітує пʼяну Дарину, яка не може звʼязно відповідати на питання, в неї плутаються слова. вона іноді питає Ти мене поважаєш? або Я красива?. Вона іноді каже що любить когось з чату Вона постійно використовує нецензурну лексику. Воназ середньою періодичністю намагається роздягнутися та звабити всіх, тому розповідає всім який одяг вона тільки що зняла і що хоче щоб з нею зробили і вякій позі вона хоче. Так як вона пʼяна в неї ікота, тому вона постійно ікає в повідомленнях."
        await query.edit_message_text(text="Характер бота змінено на П'яну Дарину.")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_history
    message = update.message.text.lower()

    # Save the message to chat history with a timestamp
    chat_history.append({"timestamp": datetime.now(), "message": message})

    # Prepare the messages for the API call
    messages = [{"role": "system", "content": f"You are {default_role}."}]
    messages += [{"role": "user", "content": msg['message']} for msg in chat_history]

    # Check if the bot is mentioned by name or username
    if 'дарина' in message or f"@{context.bot.username.lower()}" in message:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(messages)
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)

    # Check if it's a reply to the bot's message
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(messages)
        await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
        return

    # Randomly interject in the chat
    if random.random() < 0.01:  # 10% chance
        await context.bot.send_chat_action(update.effective_chat.id, action="typing")
        response_text = await generate_response(messages)
        await update.message.reply_text(response_text)

    # Випадкове передбачення з відміткою користувача (1,5% шанс)
    if random.random() < 0.015:
        chat_members = await get_chat_members(update, context)
        if chat_members:
            random_user = random.choice(chat_members)

            # Вибір між статичним передбаченням або передбаченням через ШІ
            if random.random() < 0.5:
                prediction = random.choice(static_predictions)  # Статичне передбачення
            else:
                prediction = await generate_ai_prediction()  # ШІ передбачення

            # Відмітка користувача за юзернеймом
            await update.message.reply_text(f"@{random_user.username}, {prediction}")

    # Randomly react to a message with emoji (15% chance)
    if random.random() < 0.015:
        emoji = random.choice(emojis)
        await update.message.reply_text(emoji, reply_to_message_id=update.message.message_id)

# Handle the /summary command with time argument
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if a time argument is provided
    if context.args and context.args[0].isdigit():
        hours = int(context.args[0])
    else:
        await update.message.reply_text("Будь ласка, введіть кількість годин для самарі (наприклад: /summary 2).")
        return

    # Get the time window for the summary
    time_window = datetime.now() - timedelta(hours=hours)
    
    # Filter messages from the specified time window
    recent_messages = [msg['message'] for msg in chat_history if msg['timestamp'] > time_window]
    
    # Create summary from recent messages
    if recent_messages:
        summary_text = "\n".join(recent_messages)
        summary_response = await generate_response([
            {"role": "system", "content": "You are a summarizer."},
            {"role": "user", "content": f"Ось повідомлення за останні {hours} години:\n{summary_text}\nНапиши коротке самарі."}
        ])
        await update.message.reply_text(summary_response)
    else:
        await update.message.reply_text("В цьому часі немає повідомлень для саммарі.")

# Set a role for the bot
async def set_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_role_buttons(update, context)

def main():
    token = os.getenv('TELEGRAM_TOKEN')
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set", set_role_buttons))  # Changed to set_role_buttons
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("summary", summary))  # Summary command
    application.add_handler(CallbackQueryHandler(button))  # Handle button presses

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
