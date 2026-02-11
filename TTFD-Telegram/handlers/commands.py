"""
Обработчики команд Telegram бота
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db, RANKS
from config import TELEGRAM_ADMIN_IDS, DAILY_REWARD_XP, DAILY_REWARD_COINS
from utils.tickets import get_user_tickets

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - главное меню"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Создаём/обновляем пользователя в БД
    db.update_user(
        telegram_id,
        username=user.username or 'Unknown',
        first_name=user.first_name or 'Unknown'
    )
    
    keyboard = [
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🎁 Ежедневная награда", callback_data="daily")],
        [InlineKeyboardButton("🏆 Таблица лидеров", callback_data="leaderboard")],
        [InlineKeyboardButton("🎮 Игры", callback_data="game_menu")],
        [InlineKeyboardButton("🎫 Тикеты", callback_data="tickets_menu")],
        [InlineKeyboardButton("🛒 Магазин", callback_data="shop")],
    ]
    
    # Админ-панель для админов
    if telegram_id in TELEGRAM_ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🌙 **Добро пожаловать в TTFD Bot!**

Привет, {user.first_name}! 👋

Я помогу тебе:
• Отслеживать твой прогресс и ранг
• Получать ежедневные награды
• Создавать тикеты поддержки
• Покупать предметы в магазине

Выбери действие из меню ниже:
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - справка"""
    help_text = """
📖 **Справка по командам:**

**Основные:**
/start - Главное меню
/help - Эта справка
/profile - Твой профиль
/daily - Получить ежедневную награду
/leaderboard - Таблица лидеров
/shop - Магазин предметов

**Интеграция:**
/link <discord_id> - Привязать Discord аккаунт

**Тикеты:**
/ticket - Создать тикет
/mytickets - Мои тикеты

**Для админов:**
/admin - Админ-панель
/broadcast <текст> - Рассылка всем
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profile - показать профиль"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    db_user = db.get_user(telegram_id)
    rank = db.get_rank_info(db_user['rank_id'])
    
    # Прогресс до следующего ранга
    next_rank = None
    progress_text = ""
    if db_user['rank_id'] < len(RANKS):
        next_rank = RANKS[db_user['rank_id']]
        xp_needed = next_rank['required_xp'] - db_user['xp']
        progress_text = f"\n📈 До следующего ранга: {xp_needed} XP"
    else:
        progress_text = "\n🏆 Максимальный ранг достигнут!"
    
    profile_text = f"""
👤 **Твой профиль**

🆔 ID: `{telegram_id}`
👤 Имя: {db_user['first_name']}
🎭 Username: @{db_user['username']}

⭐ Ранг: **{rank['name']}** (#{db_user['rank_id']})
✨ XP: {db_user['xp']}
💰 Монеты: {db_user['coins']}{progress_text}

🔗 Discord: {'Привязан' if db_user['discord_id'] else 'Не привязан'}
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        profile_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /daily - получить ежедневную награду"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    result = db.claim_daily(telegram_id, DAILY_REWARD_XP, DAILY_REWARD_COINS)
    
    if result['success']:
        text = f"""
🎁 **Ежедневная награда получена!**

✨ +{result['xp']} XP
💰 +{result['coins']} монет

Возвращайся завтра за новой наградой! 🌙
"""
    else:
        text = f"⏰ {result['error']}"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /leaderboard - таблица лидеров"""
    leaderboard = db.get_leaderboard(10)
    
    text = "🏆 **Таблица лидеров**\n\n"
    
    for i, user in enumerate(leaderboard, 1):
        rank = db.get_rank_info(user['rank_id'])
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} **{user['first_name']}** - {user['xp']} XP ({rank['name']})\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /link - привязать Discord аккаунт"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    if not context.args:
        text = """
🔗 **Привязка Discord аккаунта**

Использование: `/link <discord_id>`

Пример: `/link 123456789012345678`

Чтобы узнать свой Discord ID:
1. Включи режим разработчика в Discord
2. Нажми ПКМ на свой профиль
3. Выбери "Копировать ID"
"""
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    discord_id = context.args[0]
    
    # Проверка что это число
    if not discord_id.isdigit():
        await update.message.reply_text("❌ Discord ID должен быть числом!")
        return
    
    db.link_discord(telegram_id, discord_id)
    
    text = f"""
✅ **Discord аккаунт привязан!**

Discord ID: `{discord_id}`

Теперь твой прогресс синхронизирован между Telegram и Discord! 🎉
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def ticket_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /ticket - создать тикет"""
    text = """
🎫 **Создание тикета**

Отправь мне сообщение с описанием проблемы, и я создам тикет.

Пример:
"Не могу получить ежедневную награду"
"""
    
    # Устанавливаем флаг ожидания тикета
    context.user_data['waiting_for_ticket'] = True
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def mytickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /mytickets - мои тикеты"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    tickets = get_user_tickets(telegram_id)
    
    if not tickets:
        text = "📭 У тебя пока нет тикетов"
    else:
        text = "🎫 **Твои тикеты:**\n\n"
        for ticket in tickets:
            status_emoji = "✅" if ticket['status'] == 'closed' else "🔄" if ticket['status'] == 'in_progress' else "🆕"
            text += f"{status_emoji} #{ticket['id']} - {ticket['category']}\n"
            text += f"   {ticket['message'][:50]}...\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
