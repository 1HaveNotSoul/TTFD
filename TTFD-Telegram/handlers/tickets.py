"""
Обработчики тикет-системы с FSM
Версия 2.0 - полноценная система с пошаговым созданием
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.tickets import (
    create_ticket, get_ticket, get_user_tickets, get_all_tickets,
    update_ticket_status, assign_ticket, add_ticket_response, get_ticket_stats
)
from config import TELEGRAM_ADMIN_IDS

# Состояния FSM для создания тикета
TICKET_CATEGORY, TICKET_MESSAGE, TICKET_PRIORITY, TICKET_CONFIRM = range(4)

# Состояния FSM для ответа на тикет
TICKET_RESPONSE_MESSAGE = 10

# Категории тикетов
TICKET_CATEGORIES = {
    'general': '📋 Общий вопрос',
    'technical': '🔧 Техническая проблема',
    'suggestion': '💡 Предложение',
    'complaint': '⚠️ Жалоба'
}

# Приоритеты
TICKET_PRIORITIES = {
    'low': '🟢 Низкий',
    'medium': '🟡 Средний',
    'high': '🔴 Высокий'
}

# ============================================================================
# СОЗДАНИЕ ТИКЕТА (FSM)
# ============================================================================

async def ticket_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания тикета - выбор категории"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for key, value in TICKET_CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f"ticket_cat_{key}")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="ticket_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
🎫 **Создание тикета - Шаг 1/4**

Выбери категорию тикета:
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return TICKET_CATEGORY

async def ticket_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Категория выбрана - запрос текста"""
    query = update.callback_query
    await query.answer()
    
    category_key = query.data.replace('ticket_cat_', '')
    context.user_data['ticket_category'] = category_key
    context.user_data['ticket_category_name'] = TICKET_CATEGORIES[category_key]
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="ticket_cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎫 **Создание тикета - Шаг 2/4**

Категория: {TICKET_CATEGORIES[category_key]}

Теперь опиши свою проблему или вопрос подробно:
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return TICKET_MESSAGE

async def ticket_message_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Текст получен - выбор приоритета"""
    message_text = update.message.text
    
    # Проверка длины
    if len(message_text) < 10:
        await update.message.reply_text(
            "❌ Сообщение слишком короткое! Опиши проблему подробнее (минимум 10 символов)."
        )
        return TICKET_MESSAGE
    
    if len(message_text) > 1000:
        await update.message.reply_text(
            "❌ Сообщение слишком длинное! Максимум 1000 символов."
        )
        return TICKET_MESSAGE
    
    context.user_data['ticket_message'] = message_text
    
    keyboard = []
    for key, value in TICKET_PRIORITIES.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f"ticket_pri_{key}")])
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="ticket_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎫 **Создание тикета - Шаг 3/4**

Категория: {context.user_data['ticket_category_name']}
Сообщение: ✅

Выбери приоритет:
"""
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return TICKET_PRIORITY

async def ticket_priority_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приоритет выбран - подтверждение"""
    query = update.callback_query
    await query.answer()
    
    priority_key = query.data.replace('ticket_pri_', '')
    context.user_data['ticket_priority'] = priority_key
    
    keyboard = [
        [InlineKeyboardButton("✅ Создать тикет", callback_data="ticket_confirm_yes")],
        [InlineKeyboardButton("❌ Отмена", callback_data="ticket_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
🎫 **Создание тикета - Шаг 4/4 (Подтверждение)**

📋 Категория: {context.user_data['ticket_category_name']}
{TICKET_PRIORITIES[priority_key]} Приоритет

📝 Сообщение:
{context.user_data['ticket_message']}

Всё верно?
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return TICKET_CONFIRM

async def ticket_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение - создание тикета"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    # Создаём тикет
    ticket_id = create_ticket(
        telegram_id=str(user.id),
        user_name=user.first_name,
        username=user.username or 'Unknown',
        message=context.user_data['ticket_message'],
        category=context.user_data['ticket_category_name'],
        priority=context.user_data['ticket_priority']
    )
    
    # Очищаем данные
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("📋 Мои тикеты", callback_data="ticket_my_list")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"""
✅ **Тикет #{ticket_id} создан!**

Мы ответим тебе в ближайшее время.
Ты получишь уведомление, когда админ ответит на твой тикет.
"""
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    # Уведомляем админов
    await notify_admins_new_ticket(context, ticket_id)
    
    return ConversationHandler.END

async def ticket_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания тикета"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❌ Создание тикета отменено.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# ============================================================================
# ПРОСМОТР ТИКЕТОВ ПОЛЬЗОВАТЕЛЕМ
# ============================================================================

async def ticket_my_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список тикетов пользователя"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    tickets = get_user_tickets(str(user.id))
    
    if not tickets:
        keyboard = [
            [InlineKeyboardButton("➕ Создать тикет", callback_data="ticket_create_start")],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📭 У тебя пока нет тикетов",
            reply_markup=reply_markup
        )
        return
    
    text = f"🎫 **Твои тикеты ({len(tickets)}):**\n\n"
    
    keyboard = []
    for ticket in tickets[:10]:  # Показываем первые 10
        status_emoji = "✅" if ticket['status'] == 'closed' else "🔄" if ticket['status'] == 'in_progress' else "🆕"
        priority_emoji = "🔴" if ticket['priority'] == 'high' else "🟡" if ticket['priority'] == 'medium' else "🟢"
        
        text += f"{status_emoji} {priority_emoji} **#{ticket['id']}** - {ticket['category']}\n"
        text += f"   {ticket['message'][:40]}...\n\n"
        
        keyboard.append([InlineKeyboardButton(
            f"#{ticket['id']} - {ticket['category'][:15]}",
            callback_data=f"ticket_view_{ticket['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("➕ Создать тикет", callback_data="ticket_create_start")])
    keyboard.append([InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def ticket_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр конкретного тикета"""
    query = update.callback_query
    await query.answer()
    
    ticket_id = int(query.data.replace('ticket_view_', ''))
    ticket = get_ticket(ticket_id)
    
    if not ticket:
        await query.edit_message_text("❌ Тикет не найден")
        return
    
    # Проверка прав доступа
    user = query.from_user
    telegram_id = str(user.id)
    is_admin = telegram_id in TELEGRAM_ADMIN_IDS
    
    if ticket['telegram_id'] != telegram_id and not is_admin:
        await query.edit_message_text("❌ У тебя нет доступа к этому тикету")
        return
    
    status_emoji = "✅" if ticket['status'] == 'closed' else "🔄" if ticket['status'] == 'in_progress' else "🆕"
    priority_emoji = "🔴" if ticket['priority'] == 'high' else "🟡" if ticket['priority'] == 'medium' else "🟢"
    
    text = f"""
🎫 **Тикет #{ticket['id']}**

{status_emoji} Статус: {ticket['status']}
{priority_emoji} Приоритет: {ticket['priority']}
📋 Категория: {ticket['category']}
👤 От: {ticket['user_name']} (@{ticket['username']})

📝 **Сообщение:**
{ticket['message']}

"""
    
    # Ответы
    if ticket['responses']:
        text += "💬 **Ответы:**\n\n"
        for resp in ticket['responses']:
            role = "👨‍💼 Админ" if resp['is_admin'] else "👤 Пользователь"
            text += f"{role} {resp['responder_name']}:\n{resp['message']}\n\n"
    
    # Кнопки
    keyboard = []
    
    if ticket['status'] != 'closed':
        keyboard.append([InlineKeyboardButton("💬 Ответить", callback_data=f"ticket_reply_{ticket_id}")])
        keyboard.append([InlineKeyboardButton("✅ Закрыть тикет", callback_data=f"ticket_close_{ticket_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="ticket_my_list")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================================================
# ОТВЕТ НА ТИКЕТ
# ============================================================================

async def ticket_reply_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало ответа на тикет"""
    query = update.callback_query
    await query.answer()
    
    ticket_id = int(query.data.replace('ticket_reply_', ''))
    context.user_data['replying_to_ticket'] = ticket_id
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data=f"ticket_view_{ticket_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💬 Напиши свой ответ на тикет #{ticket_id}:",
        reply_markup=reply_markup
    )
    return TICKET_RESPONSE_MESSAGE

async def ticket_reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получен ответ на тикет"""
    message_text = update.message.text
    ticket_id = context.user_data.get('replying_to_ticket')
    
    if not ticket_id:
        await update.message.reply_text("❌ Ошибка: тикет не найден")
        return ConversationHandler.END
    
    user = update.effective_user
    telegram_id = str(user.id)
    is_admin = telegram_id in TELEGRAM_ADMIN_IDS
    
    # Добавляем ответ
    add_ticket_response(
        ticket_id=ticket_id,
        responder_id=telegram_id,
        responder_name=user.first_name,
        message=message_text,
        is_admin=is_admin
    )
    
    # Уведомляем другую сторону
    ticket = get_ticket(ticket_id)
    if is_admin:
        # Админ ответил - уведомляем пользователя
        await notify_user_admin_replied(context, ticket, message_text)
    else:
        # Пользователь ответил - уведомляем админов
        await notify_admins_user_replied(context, ticket, message_text)
    
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("👀 Посмотреть тикет", callback_data=f"ticket_view_{ticket_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Ответ на тикет #{ticket_id} отправлен!",
        reply_markup=reply_markup
    )
    
    return ConversationHandler.END

# ============================================================================
# ЗАКРЫТИЕ ТИКЕТА
# ============================================================================

async def ticket_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Закрыть тикет"""
    query = update.callback_query
    await query.answer()
    
    ticket_id = int(query.data.replace('ticket_close_', ''))
    ticket = get_ticket(ticket_id)
    
    if not ticket:
        await query.edit_message_text("❌ Тикет не найден")
        return
    
    # Проверка прав
    user = query.from_user
    telegram_id = str(user.id)
    is_admin = telegram_id in TELEGRAM_ADMIN_IDS
    
    if ticket['telegram_id'] != telegram_id and not is_admin:
        await query.answer("❌ У тебя нет прав закрыть этот тикет", show_alert=True)
        return
    
    update_ticket_status(ticket_id, 'closed')
    
    keyboard = [[InlineKeyboardButton("🔙 К тикетам", callback_data="ticket_my_list")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Тикет #{ticket_id} закрыт!",
        reply_markup=reply_markup
    )
    
    # Уведомляем другую сторону
    if is_admin:
        await notify_user_ticket_closed(context, ticket)
    else:
        await notify_admins_ticket_closed(context, ticket)

# ============================================================================
# АДМИН-ПАНЕЛЬ ТИКЕТОВ
# ============================================================================

async def ticket_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ-панель тикетов"""
    query = update.callback_query
    await query.answer()
    
    stats = get_ticket_stats()
    
    text = f"""
🎫 **Админ-панель тикетов**

📊 Статистика:
• Всего: {stats['total']}
• 🆕 Открыто: {stats['open']}
• 🔄 В работе: {stats['in_progress']}
• ✅ Закрыто: {stats['closed']}

🎯 По приоритету:
• 🔴 Высокий: {stats['high_priority']}
• 🟡 Средний: {stats['medium_priority']}
• 🟢 Низкий: {stats['low_priority']}
"""
    
    keyboard = [
        [InlineKeyboardButton("🆕 Открытые", callback_data="ticket_admin_list_open")],
        [InlineKeyboardButton("🔄 В работе", callback_data="ticket_admin_list_in_progress")],
        [InlineKeyboardButton("✅ Закрытые", callback_data="ticket_admin_list_closed")],
        [InlineKeyboardButton("📋 Все тикеты", callback_data="ticket_admin_list_all")],
        [InlineKeyboardButton("🔙 Админ-панель", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def ticket_admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Список тикетов для админа с фильтром"""
    query = update.callback_query
    await query.answer()
    
    # Определяем фильтр
    filter_map = {
        'ticket_admin_list_open': 'open',
        'ticket_admin_list_in_progress': 'in_progress',
        'ticket_admin_list_closed': 'closed',
        'ticket_admin_list_all': None
    }
    
    status_filter = filter_map.get(query.data)
    tickets = get_all_tickets(status_filter=status_filter)
    
    filter_name = {
        'open': '🆕 Открытые',
        'in_progress': '🔄 В работе',
        'closed': '✅ Закрытые',
        None: '📋 Все'
    }
    
    if not tickets:
        text = f"{filter_name[status_filter]} тикеты: пусто"
    else:
        text = f"🎫 **{filter_name[status_filter]} тикеты ({len(tickets)}):**\n\n"
        
        keyboard = []
        for ticket in tickets[:15]:  # Показываем первые 15
            status_emoji = "✅" if ticket['status'] == 'closed' else "🔄" if ticket['status'] == 'in_progress' else "🆕"
            priority_emoji = "🔴" if ticket['priority'] == 'high' else "🟡" if ticket['priority'] == 'medium' else "🟢"
            
            text += f"{status_emoji} {priority_emoji} **#{ticket['id']}** от {ticket['user_name']}\n"
            text += f"   {ticket['category']} - {ticket['message'][:30]}...\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"#{ticket['id']} - {ticket['user_name'][:15]}",
                callback_data=f"ticket_admin_view_{ticket['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="ticket_admin_panel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="ticket_admin_panel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def ticket_admin_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр тикета админом"""
    query = update.callback_query
    await query.answer()
    
    ticket_id = int(query.data.replace('ticket_admin_view_', ''))
    ticket = get_ticket(ticket_id)
    
    if not ticket:
        await query.edit_message_text("❌ Тикет не найден")
        return
    
    status_emoji = "✅" if ticket['status'] == 'closed' else "🔄" if ticket['status'] == 'in_progress' else "🆕"
    priority_emoji = "🔴" if ticket['priority'] == 'high' else "🟡" if ticket['priority'] == 'medium' else "🟢"
    
    text = f"""
🎫 **Тикет #{ticket['id']}** (Админ-просмотр)

{status_emoji} Статус: {ticket['status']}
{priority_emoji} Приоритет: {ticket['priority']}
📋 Категория: {ticket['category']}
👤 От: {ticket['user_name']} (@{ticket['username']})
🆔 Telegram ID: `{ticket['telegram_id']}`

📝 **Сообщение:**
{ticket['message']}

"""
    
    # Назначение
    if ticket['assigned_to']:
        text += f"👨‍💼 Назначен: {ticket['assigned_to']['admin_name']}\n\n"
    
    # Ответы
    if ticket['responses']:
        text += "💬 **Ответы:**\n\n"
        for resp in ticket['responses']:
            role = "👨‍💼 Админ" if resp['is_admin'] else "👤 Пользователь"
            text += f"{role} {resp['responder_name']}:\n{resp['message']}\n\n"
    
    # Кнопки
    keyboard = []
    
    if ticket['status'] != 'closed':
        if not ticket['assigned_to']:
            keyboard.append([InlineKeyboardButton("✋ Взять в работу", callback_data=f"ticket_admin_assign_{ticket_id}")])
        keyboard.append([InlineKeyboardButton("💬 Ответить", callback_data=f"ticket_reply_{ticket_id}")])
        keyboard.append([InlineKeyboardButton("✅ Закрыть", callback_data=f"ticket_close_{ticket_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 К списку", callback_data="ticket_admin_list_all")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def ticket_admin_assign(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ берёт тикет в работу"""
    query = update.callback_query
    await query.answer()
    
    ticket_id = int(query.data.replace('ticket_admin_assign_', ''))
    user = query.from_user
    
    assign_ticket(ticket_id, str(user.id), user.first_name)
    
    await query.answer("✅ Тикет взят в работу!", show_alert=True)
    
    # Обновляем просмотр
    context.user_data['temp_callback'] = f"ticket_admin_view_{ticket_id}"
    await ticket_admin_view(update, context)

# ============================================================================
# УВЕДОМЛЕНИЯ
# ============================================================================

async def notify_admins_new_ticket(context: ContextTypes.DEFAULT_TYPE, ticket_id: int):
    """Уведомить админов о новом тикете"""
    ticket = get_ticket(ticket_id)
    if not ticket:
        return
    
    priority_emoji = "🔴" if ticket['priority'] == 'high' else "🟡" if ticket['priority'] == 'medium' else "🟢"
    
    text = f"""
🆕 **Новый тикет #{ticket_id}**

{priority_emoji} Приоритет: {ticket['priority']}
📋 Категория: {ticket['category']}
👤 От: {ticket['user_name']} (@{ticket['username']})

📝 {ticket['message'][:100]}...
"""
    
    keyboard = [[InlineKeyboardButton("👀 Посмотреть", callback_data=f"ticket_admin_view_{ticket_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except:
            pass

async def notify_user_admin_replied(context: ContextTypes.DEFAULT_TYPE, ticket: dict, message: str):
    """Уведомить пользователя об ответе админа"""
    text = f"""
💬 **Админ ответил на твой тикет #{ticket['id']}**

📝 Ответ:
{message}
"""
    
    keyboard = [[InlineKeyboardButton("👀 Посмотреть тикет", callback_data=f"ticket_view_{ticket['id']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=int(ticket['telegram_id']),
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except:
        pass

async def notify_admins_user_replied(context: ContextTypes.DEFAULT_TYPE, ticket: dict, message: str):
    """Уведомить админов об ответе пользователя"""
    text = f"""
💬 **Пользователь ответил на тикет #{ticket['id']}**

👤 От: {ticket['user_name']}

📝 Ответ:
{message}
"""
    
    keyboard = [[InlineKeyboardButton("👀 Посмотреть", callback_data=f"ticket_admin_view_{ticket['id']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except:
            pass

async def notify_user_ticket_closed(context: ContextTypes.DEFAULT_TYPE, ticket: dict):
    """Уведомить пользователя о закрытии тикета"""
    text = f"""
✅ **Твой тикет #{ticket['id']} закрыт**

Если проблема не решена, создай новый тикет.
"""
    
    try:
        await context.bot.send_message(
            chat_id=int(ticket['telegram_id']),
            text=text,
            parse_mode='Markdown'
        )
    except:
        pass

async def notify_admins_ticket_closed(context: ContextTypes.DEFAULT_TYPE, ticket: dict):
    """Уведомить админов о закрытии тикета пользователем"""
    text = f"""
✅ **Пользователь закрыл тикет #{ticket['id']}**

👤 {ticket['user_name']} (@{ticket['username']})
"""
    
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=int(admin_id),
                text=text,
                parse_mode='Markdown'
            )
        except:
            pass
