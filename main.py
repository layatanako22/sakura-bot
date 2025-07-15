import json
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8163045913:AAHCTNVwoLB4IkDZ1vyKtcHaKHnpsO7jNnE"
OWNER_ID = 7143090611
OWNER_GROUP_ID = -1002735599328

shop_items = {
    "📈 Ежедневный буст": 150,
    "🎭 Смена роли": 300,
    "🎁 Подарок другу": 200,
    "🎟 Вход на ивент": 50,
    "⚔️ Тупой меч": 200,
    "🛡 Щит флуда": 200,
    "🧼 Иммунитет от чистки": 600,
    "💅 Скин Тейвата": 400,
    "🚫 Купи себе бан": 1000,
    "🙊 Не мутайте меня": 700,
    "👑 Роль Админа": 1500,
    "🔥 Судный День": 3000,
    "📌 Закреп сообщения": 500,
    "💬 Цитата дня от бота": 250,
    "💌 Анонимное сообщение": 200,
    "🎲 Рандомная роль": 350,
    "🔮 Пророчество": 500,
    "⚖️ Обвинение в хаосе": 250,
    "🐌 Медленный режим": 150
}

quotes = [
    "Будь собой — остальные роли уже заняты.",
    "Мудрость приходит не с возрастом, а с опытом.",
    "Ты способен на большее, чем думаешь.",
    "Каждое утро — это шанс начать заново."
]

prophecies = [
    "Сегодня удача на твоей стороне — рискни!",
    "Остерегайся поспешных решений.",
    "Неожиданная весть изменит твои планы.",
    "День для новых знакомств и творчества."
]

roles = [
    "Рыцарь Ордо Фавониус", "Дендро Архонт", "Путешественник Инадзумы",
    "Хранитель Тейвата", "Посланник Цуруми", "Оракул фатуи", "Капитан флота Бэй Доу"
]

# --- Хранилище пользователей ---
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    if str(user.id) not in users:
        users[str(user.id)] = {
            "name": user.username or user.first_name,
            "balance": 200,
            "boost_until": None
        }
        save_users(users)
        await update.message.reply_text(f"🌸 Привет, {user.first_name}! Ты зарегистрирован и получил 200 сакур.")
    else:
        await update.message.reply_text("Ты уже зарегистрирован!")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    data = users.get(str(user.id))
    if not data:
        await update.message.reply_text("Ты не зарегистрирован. Напиши /start.")
        return
    text = f"👤 Профиль @{data['name']}\n💰 Баланс: {data['balance']} 🌸"
    if data.get("boost_until"):
        text += f"\n📈 Буст до: {data['boost_until']}"
    await update.message.reply_text(text)

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(f"{item} — {price} 🌸", callback_data=f"buy_{item}")]
        for item, price in shop_items.items()
    ]
    await update.message.reply_text("🛍 Выбери товар:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- Покупка ---
async def handle_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    users = load_users()
    user_data = users.get(str(user.id))

    if not user_data:
        await query.edit_message_text("Ты не зарегистрирован. Напиши /start.")
        return

    item = query.data.replace("buy_", "").strip()
    price = shop_items.get(item)

    if not price:
        await query.edit_message_text("❌ Ошибка: товар не найден.")
        return

    if user_data["balance"] < price:
        await query.edit_message_text("❌ Недостаточно сакур.")
        return

    # Списание
    user_data["balance"] -= price

    # Логика активации буста
    if item == "📈 Ежедневный буст":
        if user_data.get("boost_until"):
            await query.edit_message_text("⚠️ У тебя уже активен буст!")
            return
        user_data["boost_until"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    save_users(users)

    await query.edit_message_text("✅ Спасибо за покупку! Ваш товар будет выдан владельцем.")

    # Лог в группу
    try:
        await context.bot.send_message(
            chat_id=OWNER_GROUP_ID,
            text=(
                f"🛍 Покупка!\n"
                f"👤 @{user.username or user.first_name} ({user.id})\n"
                f"📦 Товар: {item}\n"
                f"💰 Списано: {price} 🌸\n"
                f"💼 Остаток: {user_data['balance']} 🌸"
            )
        )
    except Exception as e:
        print(f"❌ Ошибка при логировании: {e}")

        # Обработка особых товаров
        if item == "📈 Ежедневный буст":
            if user_data.get("boost_until"):
                await query.edit_message_text("⚠️ У тебя уже активен буст!")
                return
            user_data["boost_until"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            save_users(users)
            await query.edit_message_text("✅ Буст активен! Спасибо за покупку.")
            return

        elif item == "💬 Цитата дня от бота":
            await query.edit_message_text(f"🧠 Цитата дня:\n«{random.choice(quotes)}»\nСпасибо за покупку!")
            return

        elif item == "🔮 Пророчество":
            await query.edit_message_text(f"🌌 Пророчество:\n{random.choice(prophecies)}\nСпасибо за покупку!")
            return

        elif item == "🎲 Рандомная роль":
            await query.edit_message_text(f"🎭 Твоя роль: {random.choice(roles)}\nСпасибо за покупку!")
            return

        elif item == "💌 Анонимное сообщение":
            await query.edit_message_text("✉️ Напиши своё анонимное сообщение:\n\n/sendmsg <username> <текст>")
            return

        elif item == "🎁 Подарок другу":
            await query.edit_message_text("🎁 Чтобы сделать подарок, воспользуйся командой:\n/gift <user_id> <сумма>")
            return

        # Отправка в группу
        try:
            await context.bot.send_message(
                chat_id=OWNER_GROUP_ID,
                text=(
                    f"🛍 Покупка!\n"
                    f"👤 @{user.username or user.first_name} ({user.id})\n"
                    f"📦 Товар: {item}\n"
                    f"💰 Списано: {price} 🌸\n"
                    f"💼 Остаток: {user_data['balance']} 🌸"
                )
            )
        except Exception as e:
            print(f"❌ Ошибка при логировании: {e}")

        await query.edit_message_text("✅ Спасибо за покупку! Ваш товар будет выдан владельцем.")

    # Обработка отдельных товаров
    if item == "📈 Ежедневный буст":
        if user_data.get("boost_until"):
            await query.edit_message_text("⚠️ У тебя уже активен буст!")
            return
        user_data["boost_until"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        save_users(users)
        await query.edit_message_text("✅ Буст активен! Спасибо за покупку.")
        return

    elif item == "💬 Цитата дня от бота":
        save_users(users)
        await query.edit_message_text(f"🧠 Цитата дня:\n«{random.choice(quotes)}»\nСпасибо за покупку!")
        return

    elif item == "🔮 Пророчество":
        save_users(users)
        await query.edit_message_text(f"🌌 Пророчество:\n{random.choice(prophecies)}\nСпасибо за покупку!")
        return

    elif item == "🎲 Рандомная роль":
        save_users(users)
        await query.edit_message_text(f"🎭 Твоя роль: {random.choice(roles)}\nСпасибо за покупку!")
        return

    elif item == "💌 Анонимное сообщение":
        save_users(users)
        await query.edit_message_text("✉️ Напиши своё анонимное сообщение:\n/sendmsg <username> <текст>")
        return

    elif item == "🎁 Подарок другу":
        save_users(users)
        await query.edit_message_text("🎁 Чтобы подарить сакуры другу, используй команду:\n/gift <user_id> <сумма>")
        return
    
    save_users(users)

    # после списания баланса и всех специальных веток
    try:
        await context.bot.send_message(
            chat_id=OWNER_GROUP_ID,
            text=(
                f"🛍 Покупка!\n"
                f"👤 @{user.username or user.first_name} ({user.id})\n"
                f"📦 Товар: {item}\n"
                f"💰 Списано: {price} 🌸\n"
                f"💼 Остаток: {user_data['balance']} 🌸"
            )
        )
    except Exception as e:
        # Если бот не может отправить — выведем ошибку в консоль
        print(f"❌ Не удалось отправить лог в группу {OWNER_GROUP_ID}: {e}")

    await query.edit_message_text("✅ Спасибо за покупку! Ваш товар будет выдан владельцем.")

# --- Ежедневный бонус за буст ---
async def boost_checker():
    while True:
        users = load_users()
        today = datetime.now().strftime("%Y-%m-%d")
        for uid, data in users.items():
            if data.get("boost_until") == today:
                data["balance"] += 200
                data["boost_until"] = None
        save_users(users)
        await asyncio.sleep(86400)

# --- Анонимное сообщение ---
async def send_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /sendmsg <username> <текст>")
        return

    username = context.args[0].lstrip("@")
    message = " ".join(context.args[1:])
    users = load_users()
    for uid, data in users.items():
        if data.get("name") == username:
            await context.bot.send_message(chat_id=int(uid), text=f"📩 Анонимное сообщение:\n{message}")
            await update.message.reply_text("✅ Сообщение отправлено.")
            return

    await update.message.reply_text("❌ Пользователь не найден.")

# --- Команда /give (только админ) ---
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ У тебя нет прав.")
        return

    try:
        uid = context.args[0]
        amount = int(context.args[1])
    except:
        await update.message.reply_text("❗ Формат: /give <user_id> <сумма>")
        return

    users = load_users()
    if uid not in users:
        await update.message.reply_text("❌ Пользователь не найден.")
        return

    users[uid]["balance"] += amount
    save_users(users)

    await update.message.reply_text(f"✅ Начислено {amount} 🌸 пользователю @{users[uid]['name']}")

# --- Команда /gift (подарок другу) ---
async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    user_data = users.get(str(user.id))

    if not user_data:
        await update.message.reply_text("Ты не зарегистрирован. Напиши /start.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Формат: /gift <user_id> <сумма>")
        return

    uid = context.args[0]
    try:
        amount = int(context.args[1])
    except:
        await update.message.reply_text("❗ Укажи число.")
        return

    if uid not in users:
        await update.message.reply_text("❌ Пользователь не найден.")
        return

    if amount < 200:
        await update.message.reply_text("🎁 Минимум для подарка — 200 🌸.")
        return

    if user_data["balance"] < amount:
        await update.message.reply_text("❌ Недостаточно сакур.")
        return

    user_data["balance"] -= amount
    users[uid]["balance"] += amount
    save_users(users)

    await update.message.reply_text(f"🎉 Ты передал {amount} 🌸 пользователю @{users[uid]['name']}")

# --- /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — регистрация\n"
        "/profile — профиль\n"
        "/shop — магазин\n"
        "/gift — Подарок другу\n"
        "/sendmsg — Анонимное сообщение\n"
        "/give — Начислить валюту (админ)\n"
        "/help — помощь"
    )

# --- Установка меню команд ---
async def set_menu(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Регистрация"),
        BotCommand("profile", "Профиль"),
        BotCommand("shop", "Магазин"),
        BotCommand("gift", "Подарок другу"),                # ← здесь
        BotCommand("sendmsg", "Анонимное сообщение"),
        BotCommand("give", "Начислить (админ)"),
        BotCommand("help", "Помощь")
    ])

# --- Запуск бота ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("gift", gift))
    app.add_handler(CommandHandler("give", give))
    app.add_handler(CommandHandler("sendmsg", send_anonymous))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_purchase))
    app.post_init = set_menu
    asyncio.create_task(boost_checker())
    print("✅ Бот запущен")
    await app.bot.send_message(chat_id=OWNER_GROUP_ID, text="🔔 Проверка: бот может писать в группу.")
    await app.run_polling()

# --- Запуск программы ---
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())