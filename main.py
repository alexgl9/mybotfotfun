# Додаємо глобальні змінні для зберігання контексту
user_profiles = {}  # Зберігає інформацію про користувачів
chat_topics = []    # Зберігає ключові теми бесіди

# Оновлюємо функцію handle_message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global chat_history, user_profiles, chat_topics
    user = update.message.from_user
    message = update.message.text

    # Оновлюємо профіль користувача
    if user.id not in user_profiles:
        user_profiles[user.id] = {
            'username': user.username,
            'first_name': user.first_name,
            'message_count': 0,
            'last_message': datetime.now(),
            'topics': []
        }
    
    user_profiles[user.id]['message_count'] += 1
    user_profiles[user.id]['last_message'] = datetime.now()

    # Аналізуємо повідомлення для виявлення тем
    toxic_keywords = ['пізд', 'йоб', 'гандон', 'сука', 'нах', 'хуй']
    if any(kw in message.lower() for kw in toxic_keywords):
        chat_topics.append('токсичність')
        user_profiles[user.id]['topics'].append('токсичність')

    # Зберігаємо повідомлення в історії
    chat_history.append({
        "timestamp": datetime.now(),
        "message": message,
        "user_id": user.id
    })

    # Підготовка контексту для GPT
    context_messages = [{"role": "system", "content": f"""
        {default_role}
        Контекст бесіди:
        Учасники: {', '.join([f"{u['first_name']} (@{u['username']})" for u in user_profiles.values()])}
        Основні теми: {', '.join(set(chat_topics))}
        Останні повідомлення: {', '.join([msg['message'][:20] for msg in chat_history[-3:]])}
    """}]

    # Додаємо історію повідомлень
    context_messages += [{"role": "user", "content": msg['message']} for msg in chat_history[-10:]]

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
        active_users = [u for u in user_profiles.values() 
                      if (datetime.now() - u['last_message']).total_seconds() < 3600]
        
        if active_users:
            target_user = random.choice(active_users)
            prediction = await generate_ai_prediction(target_user)
            await update.message.reply_text(f"@{target_user['username']}, {prediction}")

# Оновлюємо функцію генерації передбачень
async def generate_ai_prediction(target_user):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{
                "role": "system",
                "content": f"""
                    Ти - Дарина, токсична та саркастична.
                    Створи жорстке передбачення для {target_user['first_name']} (@{target_user['username']}).
                    Використай ці дані:
                    - Кількість повідомлень: {target_user['message_count']}
                    - Улюблені теми: {', '.join(set(target_user['topics']))}
                    Стиль: {default_role}
                """
            }]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error generating prediction: {e}")
        return random.choice(static_predictions)

# Решта коду залишається без змін...
