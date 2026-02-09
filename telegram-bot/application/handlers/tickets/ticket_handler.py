"""
Ticket Handler - система тикетов
Рефакторинг: использует централизованные callback и state_manager
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.ticket_service import TicketService
from domain.services.user_service import UserService
from domain.models.ticket import (
    CATEGORY_NAMES, PRIORITY_NAMES, STATUS_EMOJI,
    TicketCategory, TicketPriority
)
from core.exceptions import TicketError
from core.callbacks import TicketCallback, CallbackBuilder
from core.state_manager import state_manager, StateKey, StateTimeout


class TicketHandler:
    """Handler для тикетов"""
    
    def __init__(self, ticket_service: TicketService, user_service: UserService):
        self.ticket_service = ticket_service
        self.user_service = user_service
    
    # ========================================================================
    # СОЗДАНИЕ ТИКЕТА (FSM)
    # ========================================================================
    
    async def handle_create_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало создания - выбор категории"""
        query = update.callback_query
        if query:
            await query.answer()
        
        user_tg = update.effective_user
        
        # Инициализируем состояние
        state_manager.set_state(
            user_id=int(user_tg.id),
            state_key=StateKey.TICKET_CREATING,
            data={'step': 'category'},
            timeout=StateTimeout.MEDIUM  # 15 минут на создание
        )
        
        keyboard = []
        for key, value in CATEGORY_NAMES.items():
            keyboard.append([InlineKeyboardButton(value, callback_data=TicketCallback.category(key))])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=TicketCallback.cancel())])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = """
🎫 **Создание тикета - Шаг 1/4**

Выбери категорию тикета:
"""
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_category_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Категория выбрана - запрос текста"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        
        # Проверяем состояние
        state = state_manager.get_state(int(user_tg.id), StateKey.TICKET_CREATING)
        if not state:
            await query.answer("⏰ Время создания тикета истекло", show_alert=True)
            await self.handle_menu(update, context)
            return
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        category_key = params[0]
        
        # Обновляем состояние
        state_manager.update_state_data(
            int(user_tg.id),
            StateKey.TICKET_CREATING,
            {
                'step': 'message',
                'category': category_key,
                'category_name': CATEGORY_NAMES[category_key]
            }
        )
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data=TicketCallback.cancel())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
🎫 **Создание тикета - Шаг 2/4**

Категория: {CATEGORY_NAMES[category_key]}

Теперь опиши свою проблему или вопрос подробно:
(минимум 10 символов, максимум 1000)
"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_message_received(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Текст получен - выбор приоритета"""
        user_tg = update.effective_user
        message_text = update.message.text
        
        # Проверяем состояние
        state = state_manager.get_state(int(user_tg.id), StateKey.TICKET_CREATING)
        if not state or state.get('step') != 'message':
            await update.message.reply_text(
                "⏰ Время создания тикета истекло. Начни заново с /tickets"
            )
            return
        
        # Валидация
        if len(message_text) < 10:
            await update.message.reply_text(
                "❌ Сообщение слишком короткое! Опиши проблему подробнее (минимум 10 символов)."
            )
            return
        
        if len(message_text) > 1000:
            await update.message.reply_text(
                "❌ Сообщение слишком длинное! Максимум 1000 символов."
            )
            return
        
        # Обновляем состояние
        state_manager.update_state_data(
            int(user_tg.id),
            StateKey.TICKET_CREATING,
            {
                'step': 'priority',
                'message': message_text
            }
        )
        
        keyboard = []
        for key, value in PRIORITY_NAMES.items():
            keyboard.append([InlineKeyboardButton(value, callback_data=TicketCallback.priority(key))])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=TicketCallback.cancel())])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
🎫 **Создание тикета - Шаг 3/4**

Категория: {state['category_name']}
Сообщение: ✅

Выбери приоритет:
"""
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_priority_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Приоритет выбран - подтверждение"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        
        # Проверяем состояние
        state = state_manager.get_state(int(user_tg.id), StateKey.TICKET_CREATING)
        if not state or state.get('step') != 'priority':
            await query.answer("⏰ Время создания тикета истекло", show_alert=True)
            await self.handle_menu(update, context)
            return
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        priority_key = params[0]
        
        # Обновляем состояние
        state_manager.update_state_data(
            int(user_tg.id),
            StateKey.TICKET_CREATING,
            {
                'step': 'confirm',
                'priority': priority_key
            }
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Создать тикет", callback_data=TicketCallback.confirm())],
            [InlineKeyboardButton("❌ Отмена", callback_data=TicketCallback.cancel())]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
🎫 **Создание тикета - Шаг 4/4 (Подтверждение)**

📋 Категория: {state['category_name']}
{PRIORITY_NAMES[priority_key]} Приоритет

📝 Сообщение:
{state['message']}

Всё верно?
"""
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтверждение - создание тикета"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        # Получаем состояние
        state = state_manager.get_state(int(user_tg.id), StateKey.TICKET_CREATING)
        if not state or state.get('step') != 'confirm':
            await query.answer("⏰ Время создания тикета истекло", show_alert=True)
            await self.handle_menu(update, context)
            return
        
        try:
            # Создаём тикет
            ticket = await self.ticket_service.create_ticket(
                user_id=user.id,
                category=state['category'],
                priority=state['priority'],
                subject=state['message']
            )
            
            # Очищаем состояние
            state_manager.clear_state(int(user_tg.id), StateKey.TICKET_CREATING)
            
            keyboard = [
                [InlineKeyboardButton("📋 Мои тикеты", callback_data=TicketCallback.my_list())],
                [InlineKeyboardButton("👀 Посмотреть тикет", callback_data=TicketCallback.view(ticket.id))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = f"""
✅ **Тикет #{ticket.id} создан!**

Мы ответим тебе в ближайшее время.
Ты получишь уведомление, когда админ ответит на твой тикет.
"""
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        except TicketError as e:
            await query.answer(str(e), show_alert=True)
    
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена создания тикета"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        
        # Очищаем состояние
        state_manager.clear_state(int(user_tg.id), StateKey.TICKET_CREATING)
        
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=TicketCallback.menu())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Создание тикета отменено.",
            reply_markup=reply_markup
        )
    
    # ========================================================================
    # ПРОСМОТР ТИКЕТОВ
    # ========================================================================
    
    async def handle_my_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Список тикетов пользователя"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        tickets = await self.ticket_service.get_user_tickets(user.id)
        
        if not tickets:
            keyboard = [
                [InlineKeyboardButton("➕ Создать тикет", callback_data=TicketCallback.create_start())],
                [InlineKeyboardButton("🔙 Назад", callback_data=TicketCallback.menu())]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📭 У тебя пока нет тикетов",
                reply_markup=reply_markup
            )
            return
        
        text = f"🎫 **Твои тикеты ({len(tickets)}):**\n\n"
        
        keyboard = []
        for ticket in tickets[:10]:
            status_emoji = STATUS_EMOJI.get(ticket.status, '❓')
            priority_emoji = "🔴" if ticket.priority == 'high' else "🟡" if ticket.priority == 'medium' else "🟢"
            
            text += f"{status_emoji} {priority_emoji} **#{ticket.id}** - {CATEGORY_NAMES.get(ticket.category, ticket.category)}\n"
            text += f"   {ticket.subject[:40]}...\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"#{ticket.id} - {CATEGORY_NAMES.get(ticket.category, '')[:15]}",
                callback_data=TicketCallback.view(ticket.id)
            )])
        
        keyboard.append([InlineKeyboardButton("➕ Создать тикет", callback_data=TicketCallback.create_start())])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=TicketCallback.menu())])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр конкретного тикета"""
        query = update.callback_query
        await query.answer()
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        ticket_id = int(params[0])
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        # Проверка доступа
        can_access = await self.ticket_service.can_user_access_ticket(
            ticket_id, user.id, is_admin=False
        )
        
        if not can_access:
            await query.answer("❌ У тебя нет доступа к этому тикету", show_alert=True)
            return
        
        ticket = await self.ticket_service.get_ticket_with_messages(ticket_id)
        
        if not ticket:
            await query.edit_message_text("❌ Тикет не найден")
            return
        
        status_emoji = STATUS_EMOJI.get(ticket.status, '❓')
        priority_emoji = "🔴" if ticket.priority == 'high' else "🟡" if ticket.priority == 'medium' else "🟢"
        
        text = f"""
🎫 **Тикет #{ticket.id}**

{status_emoji} Статус: {ticket.status}
{priority_emoji} Приоритет: {ticket.priority}
📋 Категория: {CATEGORY_NAMES.get(ticket.category, ticket.category)}

📝 **Сообщение:**
{ticket.subject}

"""
        
        # Ответы
        if ticket.messages:
            text += "💬 **Ответы:**\n\n"
            for msg in ticket.messages:
                role = "👨‍💼 Админ" if msg.is_admin else "👤 Ты"
                text += f"{role}: {msg.message}\n\n"
        
        # Кнопки
        keyboard = []
        
        if ticket.status != 'closed':
            keyboard.append([InlineKeyboardButton("✅ Закрыть тикет", callback_data=TicketCallback.close(ticket_id))])
        
        keyboard.append([InlineKeyboardButton("🔙 К тикетам", callback_data=TicketCallback.my_list())])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_close(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Закрыть тикет"""
        query = update.callback_query
        await query.answer()
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        ticket_id = int(params[0])
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        # Проверка доступа
        can_access = await self.ticket_service.can_user_access_ticket(
            ticket_id, user.id, is_admin=False
        )
        
        if not can_access:
            await query.answer("❌ У тебя нет прав закрыть этот тикет", show_alert=True)
            return
        
        await self.ticket_service.close_ticket(ticket_id)
        
        keyboard = [[InlineKeyboardButton("🔙 К тикетам", callback_data=TicketCallback.my_list())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ Тикет #{ticket_id} закрыт!",
            reply_markup=reply_markup
        )
    
    # ========================================================================
    # МЕНЮ
    # ========================================================================
    
    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню тикетов"""
        query = update.callback_query
        if query:
            await query.answer()
        
        text = """
🎫 **Тикеты поддержки**

Есть вопрос или проблема? Создай тикет!
Мы ответим в ближайшее время.
"""
        
        keyboard = [
            [InlineKeyboardButton("➕ Создать тикет", callback_data=TicketCallback.create_start())],
            [InlineKeyboardButton("📋 Мои тикеты", callback_data=TicketCallback.my_list())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
