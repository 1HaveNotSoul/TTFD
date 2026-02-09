"""
Admin Ticket Handler - админ-панель тикетов
Рефакторинг: использует централизованные callback
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.ticket_service import TicketService
from domain.services.user_service import UserService
from domain.services.permission_service import PermissionService
from domain.models.permission import Permission
from domain.models.ticket import CATEGORY_NAMES, PRIORITY_NAMES, STATUS_EMOJI
from core.callbacks import AdminCallback, CallbackBuilder


class AdminTicketHandler:
    """Handler для админ-панели тикетов"""
    
    def __init__(self, ticket_service: TicketService, user_service: UserService):
        self.ticket_service = ticket_service
        self.user_service = user_service
    
    @PermissionService.require_permission(Permission.VIEW_TICKETS)
    async def handle_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Админ-панель тикетов"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        stats = await self.ticket_service.get_stats()
        
        text = f"""
🎫 **Админ-панель тикетов**

📊 Статистика:
• Всего: {stats.total}
• 🆕 Открыто: {stats.open}
• 🔄 В работе: {stats.in_progress}
• ✅ Закрыто: {stats.closed}

🎯 По приоритету:
• 🔴 Высокий: {stats.high_priority}
• 🟡 Средний: {stats.medium_priority}
• 🟢 Низкий: {stats.low_priority}
"""
        
        keyboard = [
            [InlineKeyboardButton("🆕 Открытые", callback_data=AdminCallback.ticket_list("open"))],
            [InlineKeyboardButton("🔄 В работе", callback_data=AdminCallback.ticket_list("in_progress"))],
            [InlineKeyboardButton("✅ Закрытые", callback_data=AdminCallback.ticket_list("closed"))],
            [InlineKeyboardButton("📋 Все тикеты", callback_data=AdminCallback.ticket_list("all"))],
            [InlineKeyboardButton("🔙 Админ-панель", callback_data=AdminCallback.panel())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @PermissionService.require_permission(Permission.VIEW_TICKETS)
    async def handle_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Список тикетов с фильтром"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        status_param = params[1] if len(params) > 1 else 'all'
        
        # Определяем фильтр
        filter_map = {
            'open': 'open',
            'in_progress': 'in_progress',
            'closed': 'closed',
            'all': None
        }
        
        status_filter = filter_map.get(status_param)
        tickets = await self.ticket_service.get_all_tickets(status=status_filter)
        
        filter_name = {
            'open': '🆕 Открытые',
            'in_progress': '🔄 В работе',
            'closed': '✅ Закрытые',
            None: '📋 Все'
        }
        
        if not tickets:
            text = f"{filter_name[status_filter]} тикеты: пусто"
            keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=AdminCallback.tickets())]]
        else:
            text = f"🎫 **{filter_name[status_filter]} тикеты ({len(tickets)}):**\n\n"
            
            keyboard = []
            for ticket in tickets[:15]:
                status_emoji = STATUS_EMOJI.get(ticket.status, '❓')
                priority_emoji = "🔴" if ticket.priority == 'high' else "🟡" if ticket.priority == 'medium' else "🟢"
                
                text += f"{status_emoji} {priority_emoji} **#{ticket.id}**\n"
                text += f"   {CATEGORY_NAMES.get(ticket.category, ticket.category)}\n"
                text += f"   {ticket.subject[:30]}...\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"#{ticket.id} - {CATEGORY_NAMES.get(ticket.category, '')[:20]}",
                    callback_data=AdminCallback.ticket_view(ticket.id)
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=AdminCallback.tickets())])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @PermissionService.require_permission(Permission.VIEW_TICKETS)
    async def handle_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр тикета админом"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        ticket_id = int(params[2])  # admin:ticket:view:123
        ticket = await self.ticket_service.get_ticket_with_messages(ticket_id)
        
        if not ticket:
            await query.edit_message_text("❌ Тикет не найден")
            return
        
        status_emoji = STATUS_EMOJI.get(ticket.status, '❓')
        priority_emoji = "🔴" if ticket.priority == 'high' else "🟡" if ticket.priority == 'medium' else "🟢"
        
        text = f"""
🎫 **Тикет #{ticket.id}** (Админ-просмотр)

{status_emoji} Статус: {ticket.status}
{priority_emoji} Приоритет: {ticket.priority}
📋 Категория: {CATEGORY_NAMES.get(ticket.category, ticket.category)}
👤 От: {ticket.user_name}

📝 **Сообщение:**
{ticket.subject}

"""
        
        # Назначение
        if ticket.assigned_to_name:
            text += f"👨‍💼 Назначен: {ticket.assigned_to_name}\n\n"
        
        # Ответы
        if ticket.messages:
            text += "💬 **Ответы:**\n\n"
            for msg in ticket.messages:
                role = "👨‍💼 Админ" if msg.is_admin else "👤 Пользователь"
                text += f"{role} {msg.user_name}: {msg.message}\n\n"
        
        # Кнопки
        keyboard = []
        
        if ticket.status != 'closed':
            if not ticket.assigned_to:
                keyboard.append([InlineKeyboardButton("✋ Взять в работу", callback_data=AdminCallback.ticket_assign(ticket_id))])
            keyboard.append([InlineKeyboardButton("✅ Закрыть", callback_data=AdminCallback.ticket_close(ticket_id))])
        
        keyboard.append([InlineKeyboardButton("🔙 К списку", callback_data=AdminCallback.ticket_list("all"))])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @PermissionService.require_permission(Permission.ASSIGN_TICKETS)
    async def handle_assign(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Админ берёт тикет в работу"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        ticket_id = int(params[2])  # admin:ticket:assign:123
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        await self.ticket_service.assign_ticket(ticket_id, user.id)
        
        await query.answer("✅ Тикет взят в работу!", show_alert=True)
        
        # Обновляем просмотр - создаём временный callback
        update.callback_query.data = AdminCallback.ticket_view(ticket_id)
        await self.handle_view(update, context)
    
    @PermissionService.require_permission(Permission.CLOSE_TICKETS)
    async def handle_close(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Закрыть тикет"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        # Парсим callback
        _, _, params = CallbackBuilder.parse(query.data)
        ticket_id = int(params[2])  # admin:ticket:close:123
        
        await self.ticket_service.close_ticket(ticket_id)
        
        keyboard = [[InlineKeyboardButton("🔙 К списку", callback_data=AdminCallback.ticket_list("all"))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ Тикет #{ticket_id} закрыт!",
            reply_markup=reply_markup
        )
