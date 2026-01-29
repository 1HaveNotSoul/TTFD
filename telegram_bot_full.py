# Полноценный Telegram бот с кнопками, тикетами и админ-панелью
import os
import json
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_IDS = [int(x) for x in os.getenv('TELEGRAM_ADMIN_IDS', '').split(',') if x.strip()]

# Хранилище тикетов
TICKETS_FILE = 'tickets.json'
tickets = {}

# Импорт базы данных Discord сервера
try:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from database import db, RANKS
    DB_AVAILABLE = True
    print("✅ База данных Discord подключена")
except Exception as e:
    print(f"⚠️ База данных Discord недоступна: {e}")
    DB_AVAILABLE = False
    db = None
    RANKS = []

def load_tickets():
    """Загрузить тикеты из файла"""
    global tickets
    try:
        if os.path.exists(TICKETS_FILE):
            with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
                tickets = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка загрузки тикетов: {e}")
        tickets = {}

def save_tickets():
    """Сохранить тикеты в файл"""
    try:
        with open(TICKETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(tickets, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Ошибка сохранения тикетов: {e}")

def is_admin(user_id):
    """Проверить является ли пользователь админом"""
    return user_id in ADMIN_IDS

# ==================== ГЛАВНОЕ МЕНЮ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - главное меню"""
    try:
        print(f"📥 Получена команда /start от {update.effective_user.id}")
        user = update.effective_user
        
        keyboard = [
            [InlineKeyboardButton("👤 Мой профиль", callback_data='profile')],
            [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
            [InlineKeyboardButton("🎫 Создать тикет", callback_data='create_ticket')],
            [InlineKeyboardButton("📋 Мои тикеты", callback_data='my_tickets')],
        ]
        
        # Админ кнопки
        if is_admin(user.id):
            keyboard.append([InlineKeyboardButton("🔧 Админ-панель", callback_data='admin_panel')])
            print(f"✅ Пользователь {user.id} - админ")
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"👋 Привет, {user.first_name}!\n\n"
        text += "🎮 Добро пожаловать в TTFD Bot!\n\n"
        text += "Выбери действие:"
        
        if update.message:
            await update.message.reply_text(text, reply_markup=reply_markup)
            print(f"✅ Отправлен ответ пользователю {user.id}")
        else:
            await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
            print(f"✅ Обновлено сообщение для {user.id}")
    except Exception as e:
        print(f"❌ Ошибка в start: {e}")
        import traceback
        traceback.print_exc()

# ==================== ПРОФИЛЬ ====================

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    text = f"👤 <b>Твой профиль</b>\n\n"
    text += f"🆔 Telegram ID: <code>{user.id}</code>\n"
    text += f"👤 Имя: {user.first_name}\n"
    if user.username:
        text += f"📝 Username: @{user.username}\n"
    
    # Получаем данные из БД Discord сервера
    if DB_AVAILABLE and db:
        try:
            # Ищем пользователя по Telegram ID в аккаунтах
            discord_user = None
            for acc in db.accounts.get('accounts', {}).values():
                # Можно добавить поле telegram_id в аккаунты для связи
                # Пока ищем по Discord ID если он есть
                if acc.get('discord_id'):
                    user_data = db.get_user(acc['discord_id'])
                    if user_data:
                        discord_user = user_data
                        break
            
            # Если не нашли по аккаунтам, пробуем напрямую по Telegram ID
            if not discord_user:
                user_data = db.get_user(str(user.id))
                if user_data and user_data.get('xp', 0) > 0:  # Проверяем что это реальный пользователь
                    discord_user = user_data
            
            if discord_user:
                rank = db.get_rank_info(discord_user['rank_id'])
                
                text += f"\n🎮 <b>Данные Discord сервера:</b>\n"
                text += f"⭐ Опыт: <b>{discord_user['xp']}</b> XP\n"
                text += f"🏆 Ранг: <b>{rank['name']}</b>\n"
                text += f"💰 Монеты: <b>{discord_user['coins']}</b>\n"
                text += f"🖱️ Кликов: <b>{discord_user['clicks']}</b>\n"
                text += f"✅ Заданий выполнено: <b>{discord_user['tasks_completed']}</b>\n"
                
                # Прогресс до следующего ранга
                if discord_user['rank_id'] < len(RANKS):
                    next_rank = RANKS[discord_user['rank_id']]
                    xp_needed = next_rank['required_xp'] - discord_user['xp']
                    if xp_needed > 0:
                        text += f"\n📈 До следующего ранга: <b>{xp_needed}</b> XP"
            else:
                text += f"\n⚠️ Профиль Discord не найден\n"
                text += f"Играй на сервере чтобы получить статистику!"
        except Exception as e:
            print(f"❌ Ошибка получения профиля: {e}")
            text += f"\n⚠️ Ошибка загрузки данных Discord"
    else:
        text += f"\n⚠️ База данных Discord недоступна"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

# ==================== СТАТИСТИКА ====================

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    query = update.callback_query
    await query.answer()
    
    text = "📊 <b>Статистика Discord сервера</b>\n\n"
    
    if DB_AVAILABLE and db:
        try:
            # Получаем статистику из БД
            users = db.data.get('users', {})
            accounts = db.accounts.get('accounts', {})
            global_stats = db.data.get('global_stats', {})
            
            # Подсчитываем общую статистику
            total_users = len(users)
            total_accounts = len(accounts)
            total_xp = sum(u.get('xp', 0) for u in users.values())
            total_coins = sum(u.get('coins', 0) for u in users.values())
            total_clicks = global_stats.get('total_clicks', 0)
            total_tasks = global_stats.get('total_tasks_completed', 0)
            
            # Топ игрок
            top_player = None
            if users:
                top_player = max(users.values(), key=lambda x: x.get('xp', 0))
            
            text += f"👥 Всего пользователей: <b>{total_users}</b>\n"
            text += f"📝 Зарегистрированных аккаунтов: <b>{total_accounts}</b>\n"
            text += f"⭐ Всего опыта: <b>{total_xp:,}</b> XP\n"
            text += f"💰 Всего монет: <b>{total_coins:,}</b>\n"
            text += f"🖱️ Всего кликов: <b>{total_clicks:,}</b>\n"
            text += f"✅ Заданий выполнено: <b>{total_tasks}</b>\n"
            
            if top_player:
                rank = db.get_rank_info(top_player['rank_id'])
                text += f"\n🏆 <b>Топ игрок:</b>\n"
                text += f"👤 {top_player.get('username', 'Unknown')}\n"
                text += f"⭐ {top_player['xp']} XP\n"
                text += f"🏆 {rank['name']}\n"
            
            # Статистика по рангам
            rank_distribution = {}
            for user in users.values():
                rank_id = user.get('rank_id', 1)
                rank_distribution[rank_id] = rank_distribution.get(rank_id, 0) + 1
            
            if rank_distribution:
                text += f"\n📊 <b>Распределение по рангам:</b>\n"
                for rank_id in sorted(rank_distribution.keys(), reverse=True)[:5]:
                    rank = db.get_rank_info(rank_id)
                    count = rank_distribution[rank_id]
                    text += f"• {rank['name']}: {count} игроков\n"
                    
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            import traceback
            traceback.print_exc()
            text += "⚠️ Ошибка загрузки статистики"
    else:
        text += "⚠️ База данных Discord недоступна"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

# ==================== ТИКЕТЫ ====================

async def create_ticket_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание тикета"""
    query = update.callback_query
    await query.answer()
    
    text = "🎫 <b>Создание тикета</b>\n\n"
    text += "Выбери категорию проблемы:"
    
    keyboard = [
        [InlineKeyboardButton("🐛 Баг/Ошибка", callback_data='ticket_bug')],
        [InlineKeyboardButton("💡 Предложение", callback_data='ticket_suggestion')],
        [InlineKeyboardButton("❓ Вопрос", callback_data='ticket_question')],
        [InlineKeyboardButton("⚠️ Жалоба", callback_data='ticket_complaint')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def ticket_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Категория тикета выбрана"""
    query = update.callback_query
    await query.answer()
    
    category_map = {
        'ticket_bug': '🐛 Баг/Ошибка',
        'ticket_suggestion': '💡 Предложение',
        'ticket_question': '❓ Вопрос',
        'ticket_complaint': '⚠️ Жалоба'
    }
    
    category = category_map.get(query.data, 'Другое')
    context.user_data['ticket_category'] = category
    
    text = f"🎫 <b>Создание тикета</b>\n\n"
    text += f"Категория: {category}\n\n"
    text += "Теперь напиши описание проблемы:"
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # Устанавливаем флаг ожидания сообщения
    context.user_data['waiting_for_ticket'] = True

async def handle_ticket_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка сообщения с описанием тикета"""
    if not context.user_data.get('waiting_for_ticket'):
        return
    
    user = update.effective_user
    category = context.user_data.get('ticket_category', 'Другое')
    description = update.message.text
    
    # Создаём тикет
    ticket_id = f"T{len(tickets) + 1:04d}"
    tickets[ticket_id] = {
        'id': ticket_id,
        'user_id': user.id,
        'username': user.username or user.first_name,
        'category': category,
        'description': description,
        'status': 'open',
        'created_at': datetime.now().isoformat(),
        'messages': []
    }
    save_tickets()
    
    # Уведомляем пользователя
    text = f"✅ <b>Тикет создан!</b>\n\n"
    text += f"🎫 ID: <code>{ticket_id}</code>\n"
    text += f"📁 Категория: {category}\n"
    text += f"📝 Описание: {description}\n\n"
    text += "Ожидай ответа от администрации!"
    
    keyboard = [[InlineKeyboardButton("◀️ В меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    
    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            admin_text = f"🎫 <b>Новый тикет!</b>\n\n"
            admin_text += f"ID: <code>{ticket_id}</code>\n"
            admin_text += f"От: {user.first_name} (@{user.username or 'нет'})\n"
            admin_text += f"Категория: {category}\n"
            admin_text += f"Описание: {description}"
            
            admin_keyboard = [[InlineKeyboardButton("📋 Открыть тикет", callback_data=f'admin_ticket_{ticket_id}')]]
            admin_markup = InlineKeyboardMarkup(admin_keyboard)
            
            await context.bot.send_message(admin_id, admin_text, reply_markup=admin_markup, parse_mode='HTML')
        except:
            pass
    
    # Сбрасываем флаг
    context.user_data['waiting_for_ticket'] = False

async def show_my_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать тикеты пользователя"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_tickets = [t for t in tickets.values() if t['user_id'] == user_id]
    
    if not user_tickets:
        text = "📋 <b>Твои тикеты</b>\n\n"
        text += "У тебя пока нет тикетов."
        
        keyboard = [
            [InlineKeyboardButton("🎫 Создать тикет", callback_data='create_ticket')],
            [InlineKeyboardButton("◀️ Назад", callback_data='back_to_menu')]
        ]
    else:
        text = "📋 <b>Твои тикеты</b>\n\n"
        
        keyboard = []
        for ticket in sorted(user_tickets, key=lambda x: x['created_at'], reverse=True):
            status_emoji = "🟢" if ticket['status'] == 'open' else "🔴" if ticket['status'] == 'closed' else "🟡"
            keyboard.append([InlineKeyboardButton(
                f"{status_emoji} {ticket['id']} - {ticket['category']}", 
                callback_data=f"view_ticket_{ticket['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def view_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр тикета"""
    query = update.callback_query
    await query.answer()
    
    ticket_id = query.data.replace('view_ticket_', '')
    ticket = tickets.get(ticket_id)
    
    if not ticket:
        await query.message.edit_text("❌ Тикет не найден")
        return
    
    status_map = {'open': '🟢 Открыт', 'in_progress': '🟡 В работе', 'closed': '🔴 Закрыт'}
    
    text = f"🎫 <b>Тикет {ticket['id']}</b>\n\n"
    text += f"📁 Категория: {ticket['category']}\n"
    text += f"📊 Статус: {status_map.get(ticket['status'], 'Неизвестно')}\n"
    text += f"📅 Создан: {ticket['created_at'][:10]}\n\n"
    text += f"📝 Описание:\n{ticket['description']}\n\n"
    
    if ticket['messages']:
        text += "💬 <b>Сообщения:</b>\n"
        for msg in ticket['messages'][-3:]:  # Последние 3 сообщения
            text += f"• {msg['from']}: {msg['text']}\n"
    
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='my_tickets')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

# ==================== АДМИН-ПАНЕЛЬ ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-панель"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.message.edit_text("❌ У тебя нет прав администратора")
        return
    
    text = "🔧 <b>Админ-панель</b>\n\n"
    text += f"📊 Открытых тикетов: {len([t for t in tickets.values() if t['status'] == 'open'])}\n"
    text += f"📋 Всего тикетов: {len(tickets)}\n"
    
    keyboard = [
        [InlineKeyboardButton("🎫 Все тикеты", callback_data='admin_all_tickets')],
        [InlineKeyboardButton("💾 Просмотр БД", callback_data='admin_view_db')],
        [InlineKeyboardButton("◀️ Назад", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def admin_all_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все тикеты (админ)"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    if not tickets:
        text = "📋 <b>Все тикеты</b>\n\nТикетов пока нет."
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data='admin_panel')]]
    else:
        text = "📋 <b>Все тикеты</b>\n\n"
        
        keyboard = []
        for ticket in sorted(tickets.values(), key=lambda x: x['created_at'], reverse=True)[:10]:
            status_emoji = "🟢" if ticket['status'] == 'open' else "🔴" if ticket['status'] == 'closed' else "🟡"
            keyboard.append([InlineKeyboardButton(
                f"{status_emoji} {ticket['id']} - {ticket['username']}", 
                callback_data=f"admin_ticket_{ticket['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def admin_view_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр тикета (админ)"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    ticket_id = query.data.replace('admin_ticket_', '')
    ticket = tickets.get(ticket_id)
    
    if not ticket:
        await query.message.edit_text("❌ Тикет не найден")
        return
    
    status_map = {'open': '🟢 Открыт', 'in_progress': '🟡 В работе', 'closed': '🔴 Закрыт'}
    
    text = f"🎫 <b>Тикет {ticket['id']}</b>\n\n"
    text += f"👤 От: {ticket['username']} (ID: {ticket['user_id']})\n"
    text += f"📁 Категория: {ticket['category']}\n"
    text += f"📊 Статус: {status_map.get(ticket['status'], 'Неизвестно')}\n"
    text += f"📅 Создан: {ticket['created_at'][:10]}\n\n"
    text += f"📝 Описание:\n{ticket['description']}"
    
    keyboard = [
        [InlineKeyboardButton("✅ Закрыть тикет", callback_data=f"admin_close_{ticket_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_all_tickets')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

async def admin_close_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Закрыть тикет (админ)"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    ticket_id = query.data.replace('admin_close_', '')
    ticket = tickets.get(ticket_id)
    
    if ticket:
        ticket['status'] = 'closed'
        save_tickets()
        
        # Уведомляем пользователя
        try:
            await context.bot.send_message(
                ticket['user_id'],
                f"✅ Твой тикет <code>{ticket_id}</code> был закрыт администратором.",
                parse_mode='HTML'
            )
        except:
            pass
        
        await query.answer("✅ Тикет закрыт!")
        await admin_view_ticket(update, context)

async def admin_view_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр БД (админ)"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        return
    
    text = "💾 <b>Просмотр базы данных</b>\n\n"
    
    if DB_AVAILABLE and db:
        try:
            users = db.data.get('users', {})
            accounts = db.accounts.get('accounts', {})
            sessions = db.accounts.get('sessions', {})
            global_stats = db.data.get('global_stats', {})
            
            # Основная статистика
            text += "📊 <b>Общая статистика:</b>\n"
            text += f"👥 Пользователей Discord: <b>{len(users)}</b>\n"
            text += f"📝 Аккаунтов на сайте: <b>{len(accounts)}</b>\n"
            text += f"🔐 Активных сессий: <b>{len(sessions)}</b>\n"
            text += f"🎫 Тикетов: <b>{len(tickets)}</b>\n"
            
            # Игровая статистика
            text += f"\n🎮 <b>Игровая статистика:</b>\n"
            total_xp = sum(u.get('xp', 0) for u in users.values())
            total_coins = sum(u.get('coins', 0) for u in users.values())
            total_clicks = global_stats.get('total_clicks', 0)
            total_tasks = global_stats.get('total_tasks_completed', 0)
            
            text += f"⭐ Всего XP: <b>{total_xp:,}</b>\n"
            text += f"💰 Всего монет: <b>{total_coins:,}</b>\n"
            text += f"🖱️ Всего кликов: <b>{total_clicks:,}</b>\n"
            text += f"✅ Заданий выполнено: <b>{total_tasks}</b>\n"
            
            # Средние значения
            if users:
                avg_xp = total_xp // len(users)
                avg_coins = total_coins // len(users)
                text += f"\n📈 <b>Средние значения:</b>\n"
                text += f"⭐ Средний XP: <b>{avg_xp}</b>\n"
                text += f"💰 Средние монеты: <b>{avg_coins}</b>\n"
            
            # Топ-5 игроков
            if users:
                top_users = sorted(users.values(), key=lambda x: x.get('xp', 0), reverse=True)[:5]
                text += f"\n🏆 <b>Топ-5 игроков:</b>\n"
                medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                for i, user in enumerate(top_users):
                    rank = db.get_rank_info(user['rank_id'])
                    text += f"{medals[i]} {user.get('username', 'Unknown')}\n"
                    text += f"   ⭐ {user['xp']:,} XP | 💰 {user['coins']:,} | 🏆 {rank['name']}\n"
            
            # Статистика по рангам
            rank_distribution = {}
            for user in users.values():
                rank_id = user.get('rank_id', 1)
                rank_distribution[rank_id] = rank_distribution.get(rank_id, 0) + 1
            
            if rank_distribution:
                text += f"\n📊 <b>Распределение по рангам:</b>\n"
                for rank_id in sorted(rank_distribution.keys(), reverse=True)[:7]:
                    rank = db.get_rank_info(rank_id)
                    count = rank_distribution[rank_id]
                    percentage = (count / len(users)) * 100
                    text += f"• {rank['name']}: {count} ({percentage:.1f}%)\n"
            
            # Информация об аккаунтах
            if accounts:
                text += f"\n📝 <b>Аккаунты на сайте:</b>\n"
                linked_accounts = sum(1 for acc in accounts.values() if acc.get('discord_id'))
                text += f"🔗 Привязано к Discord: <b>{linked_accounts}/{len(accounts)}</b>\n"
                
        except Exception as e:
            print(f"❌ Ошибка просмотра БД: {e}")
            import traceback
            traceback.print_exc()
            text += "⚠️ Ошибка загрузки данных БД"
    else:
        text += "⚠️ База данных Discord недоступна\n"
        text += "Убедись что бот запущен в той же директории что и Discord бот"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data='admin_view_db')],
        [InlineKeyboardButton("◀️ Назад", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')

# ==================== ОБРАБОТЧИКИ ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех кнопок"""
    query = update.callback_query
    
    if query.data == 'back_to_menu':
        await start(update, context)
    elif query.data == 'profile':
        await show_profile(update, context)
    elif query.data == 'stats':
        await show_stats(update, context)
    elif query.data == 'create_ticket':
        await create_ticket_start(update, context)
    elif query.data.startswith('ticket_'):
        await ticket_category_selected(update, context)
    elif query.data == 'my_tickets':
        await show_my_tickets(update, context)
    elif query.data.startswith('view_ticket_'):
        await view_ticket(update, context)
    elif query.data == 'admin_panel':
        await admin_panel(update, context)
    elif query.data == 'admin_all_tickets':
        await admin_all_tickets(update, context)
    elif query.data.startswith('admin_ticket_'):
        await admin_view_ticket(update, context)
    elif query.data.startswith('admin_close_'):
        await admin_close_ticket(update, context)
    elif query.data == 'admin_view_db':
        await admin_view_db(update, context)

# ==================== КОМАНДЫ ====================

async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда !link - получить ссылку на сайт"""
    user = update.effective_user
    
    text = f"🌐 <b>Ссылка на сайт TTFD</b>\n\n"
    text += f"🔗 <a href='https://ttfd.onrender.com/'>https://ttfd.onrender.com/</a>\n\n"
    text += f"📱 Доступные разделы:\n"
    text += f"• <a href='https://ttfd.onrender.com/game'>Игры</a>\n"
    text += f"• <a href='https://ttfd.onrender.com/leaderboard'>Таблица лидеров</a>\n"
    text += f"• <a href='https://ttfd.onrender.com/ranks'>Ранги</a>\n"
    text += f"• <a href='https://ttfd.onrender.com/login'>Вход</a>\n"
    text += f"• <a href='https://ttfd.onrender.com/register'>Регистрация</a>\n\n"
    text += f"✨ Войди через Discord одним кликом!"
    
    keyboard = [[InlineKeyboardButton("🌐 Открыть сайт", url='https://ttfd.onrender.com/')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=False)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - список команд"""
    text = "📋 <b>Доступные команды:</b>\n\n"
    text += "/start - Главное меню\n"
    text += "/help - Список команд\n"
    text += "!link - Получить ссылку на сайт\n\n"
    text += "🎮 Используй кнопки для навигации!"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def handle_text_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых команд (!link и т.д.)"""
    text = update.message.text.strip().lower()
    
    if text == '!link':
        await link_command(update, context)
    elif not context.user_data.get('waiting_for_ticket'):
        # Если не ждём тикет, показываем подсказку
        await update.message.reply_text(
            "💡 Используй /start для открытия меню\n"
            "Или !link для получения ссылки на сайт"
        )

# ==================== ЗАПУСК БОТА ====================

def run_telegram_bot():
    """Запустить Telegram бота"""
    print("=" * 50)
    print("🤖 Запуск Telegram бота...")
    print("=" * 50)
    
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        print("   Установи переменную окружения TELEGRAM_BOT_TOKEN")
        return
    
    print(f"✅ Токен найден: {TELEGRAM_TOKEN[:10]}...")
    print(f"✅ Админы: {ADMIN_IDS}")
    
    load_tickets()
    print(f"✅ Загружено тикетов: {len(tickets)}")
    
    try:
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Команды
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        print("✅ Команды зарегистрированы")
        
        # Кнопки
        app.add_handler(CallbackQueryHandler(button_handler))
        print("✅ Обработчик кнопок зарегистрирован")
        
        # Сообщения (для тикетов и команд)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: 
            handle_ticket_message(u, c) if c.user_data.get('waiting_for_ticket') else handle_text_commands(u, c)
        ))
        print("✅ Обработчик сообщений зарегистрирован")
        
        print("=" * 50)
        print("✅ Telegram бот запущен и готов к работе!")
        print("   Отправь /start боту в Telegram")
        print("=" * 50)
        
        # Используем webhook вместо polling для работы в потоке
        # Но для простоты просто запускаем в новом event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def start_bot():
            await app.initialize()
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            # Держим бота запущенным
            await asyncio.Event().wait()
        
        loop.run_until_complete(start_bot())
    except Exception as e:
        print(f"❌ Ошибка запуска Telegram бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_telegram_bot()
