"""
Обработчик кнопок (Inline Keyboard)
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db, RANKS
from config import TELEGRAM_ADMIN_IDS, DAILY_REWARD_XP, DAILY_REWARD_COINS
from utils.tickets import get_user_tickets, get_all_tickets
from utils.shop import get_shop_items

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех кнопок"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    data = query.data
    
    # Главное меню
    if data == "back_to_menu":
        await show_main_menu(query, user)
    
    # Профиль
    elif data == "profile":
        await show_profile(query, telegram_id)
    
    # Статистика
    elif data == "stats":
        await show_stats(query)
    
    # Ежедневная награда
    elif data == "daily":
        await claim_daily_reward(query, telegram_id)
    
    # Таблица лидеров
    elif data == "leaderboard":
        await show_leaderboard(query)
    
    # Игры - перенаправляем в handlers/games.py
    elif data == "game_menu":
        from handlers.games import games_menu
        await games_menu(update, context)
    
    elif data == "game_stats":
        from handlers.games import game_stats
        await game_stats(update, context)
    
    elif data == "game_spin_start":
        from handlers.games import game_spin_start
        await game_spin_start(update, context)
    
    elif data == "game_spin_do":
        from handlers.games import game_spin_do
        await game_spin_do(update, context)
    
    # Тикеты - перенаправляем в handlers/tickets.py
    elif data == "tickets_menu":
        await show_tickets_menu(query, telegram_id)
    
    elif data == "ticket_my_list":
        from handlers.tickets import ticket_my_list
        await ticket_my_list(update, context)
    
    elif data.startswith("ticket_view_"):
        from handlers.tickets import ticket_view
        await ticket_view(update, context)
    
    elif data.startswith("ticket_close_"):
        from handlers.tickets import ticket_close
        await ticket_close(update, context)
    
    elif data == "ticket_admin_panel":
        from handlers.tickets import ticket_admin_panel
        await ticket_admin_panel(update, context)
    
    elif data.startswith("ticket_admin_list"):
        from handlers.tickets import ticket_admin_list
        await ticket_admin_list(update, context)
    
    elif data.startswith("ticket_admin_view_"):
        from handlers.tickets import ticket_admin_view
        await ticket_admin_view(update, context)
    
    elif data.startswith("ticket_admin_assign_"):
        from handlers.tickets import ticket_admin_assign
        await ticket_admin_assign(update, context)
    
    # Магазин - перенаправляем в handlers/shop.py
    elif data == "shop" or data == "shop_menu":
        from handlers.shop import shop_menu_handler
        await shop_menu_handler(update, context)
    
    # Админ-панель
    elif data == "admin":
        if telegram_id in TELEGRAM_ADMIN_IDS:
            await show_admin_panel(query)
        else:
            await query.edit_message_text("❌ У тебя нет доступа к админ-панели")
    
    elif data == "admin_users":
        if telegram_id in TELEGRAM_ADMIN_IDS:
            await show_admin_users(query)
    
    elif data == "admin_tickets":
        if telegram_id in TELEGRAM_ADMIN_IDS:
            from handlers.tickets import ticket_admin_panel
            await ticket_admin_panel(update, context)


async def show_main_menu(query, user):
    """Показать главное меню"""
    telegram_id = str(user.id)
    
    keyboard = [
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🎁 Ежедневная награда", callback_data="daily")],
        [InlineKeyboardButton("🏆 Таблица лидеров", callback_data="leaderboard")],
        [InlineKeyboardButton("🎮 Игры", callback_data="game_menu")],
        [InlineKeyboardButton("🎫 Тикеты", callback_data="tickets_menu")],
        [InlineKeyboardButton("🛒 Магазин", callback_data="shop")],
    ]
    
    if telegram_id in TELEGRAM_ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ Админ-панель", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🌙 **TTFD Bot - Главное меню**

Привет, {user.first_name}! 👋

Выбери действие из меню ниже:
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_profile(query, telegram_id):
    """Показать профиль"""
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
    
    await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_stats(query):
    """Показать глобальную статистику"""
    all_users = db.get_all_users()
    global_stats = db.data['global_stats']
    
    text = f"""
📊 **Глобальная статистика**

👥 Всего пользователей: {global_stats['total_users']}
✨ Всего заработано XP: {global_stats['total_xp_earned']}
💰 Всего заработано монет: {global_stats['total_coins_earned']}

📈 Средний XP на пользователя: {global_stats['total_xp_earned'] // max(global_stats['total_users'], 1)}
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')


async def claim_daily_reward(query, telegram_id):
    """Получить ежедневную награду"""
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
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_leaderboard(query):
    """Показать таблицу лидеров"""
    leaderboard = db.get_leaderboard(10)
    
    text = "🏆 **Таблица лидеров**\n\n"
    
    for i, user in enumerate(leaderboard, 1):
        rank = db.get_rank_info(user['rank_id'])
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} **{user['first_name']}** - {user['xp']} XP ({rank['name']})\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_tickets_menu(query, telegram_id):
    """Показать меню тикетов"""
    text = """
🎫 **Система тикетов**

Выбери действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("➕ Создать тикет", callback_data="create_ticket")],
        [InlineKeyboardButton("📋 Мои тикеты", callback_data="my_tickets")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_my_tickets(query, telegram_id):
    """Показать тикеты пользователя"""
    tickets = get_user_tickets(telegram_id)
    
    if not tickets:
        text = "📭 У тебя пока нет тикетов"
    else:
        text = "🎫 **Твои тикеты:**\n\n"
        for ticket in tickets:
            status_emoji = "✅" if ticket['status'] == 'closed' else "🔄" if ticket['status'] == 'in_progress' else "🆕"
            text += f"{status_emoji} #{ticket['id']} - {ticket['category']}\n"
            text += f"   {ticket['message'][:50]}...\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="tickets_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_shop(query, telegram_id):
    """Показать магазин"""
    items = get_shop_items()
    db_user = db.get_user(telegram_id)
    
    text = f"🛒 **Магазин предметов**\n\n💰 Твои монеты: {db_user['coins']}\n\n"
    
    for item in items:
        text += f"**{item['name']}** - {item['price']} 💰\n"
        text += f"   {item['description']}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_panel(query):
    """Показать админ-панель"""
    text = """
⚙️ **Админ-панель**

Выбери действие:
"""
    
    keyboard = [
        [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton("🎫 Тикеты", callback_data="ticket_admin_panel")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_users(query):
    """Показать список пользователей"""
    all_users = db.get_all_users()
    
    text = f"👥 **Всего пользователей: {len(all_users)}**\n\n"
    
    for user in all_users[:10]:
        rank = db.get_rank_info(user['rank_id'])
        text += f"• {user['first_name']} (@{user['username']})\n"
        text += f"  XP: {user['xp']} | Монеты: {user['coins']} | Ранг: {rank['name']}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_admin_tickets(query):
    """Показать все тикеты"""
    tickets = get_all_tickets()
    
    if not tickets:
        text = "📭 Тикетов пока нет"
    else:
        text = f"🎫 **Всего тикетов: {len(tickets)}**\n\n"
        for ticket in tickets[:10]:
            status_emoji = "✅" if ticket['status'] == 'closed' else "🔄" if ticket['status'] == 'in_progress' else "🆕"
            text += f"{status_emoji} #{ticket['id']} - {ticket['category']}\n"
            text += f"   От: {ticket['user_name']}\n"
            text += f"   {ticket['message'][:50]}...\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
