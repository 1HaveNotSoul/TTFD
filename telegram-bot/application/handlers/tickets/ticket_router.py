"""
Ticket Router - маршрутизация всех ticket callback
Централизованная регистрация handlers для домена TICKET
"""
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
import logging

from core.callbacks import CallbackBuilder, CallbackDomain
from application.handlers.tickets.ticket_handler import TicketHandler
from application.handlers.tickets.admin_ticket_handler import AdminTicketHandler

logger = logging.getLogger(__name__)


class TicketRouter:
    """
    Роутер для всех тикетных callback
    
    Обрабатывает все callback с доменом TICKET:
    - ticket:menu - главное меню тикетов
    - ticket:create:start - начало создания
    - ticket:cat:* - выбор категории
    - ticket:pri:* - выбор приоритета
    - ticket:confirm - подтверждение
    - ticket:cancel - отмена
    - ticket:my:list - список тикетов
    - ticket:view:* - просмотр тикета
    - ticket:close:* - закрыть тикет
    """
    
    def __init__(
        self,
        ticket_handler: TicketHandler,
        admin_handler: AdminTicketHandler
    ):
        self.ticket_handler = ticket_handler
        self.admin_handler = admin_handler
    
    async def route(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Маршрутизировать тикетный callback к нужному handler
        
        Args:
            update: Telegram Update
            context: Telegram Context
        """
        query = update.callback_query
        
        if not query:
            return
        
        callback_data = query.data
        
        try:
            domain, action, params = CallbackBuilder.parse(callback_data)
            
            # Проверяем что это тикетный callback
            if domain != CallbackDomain.TICKET.value:
                logger.warning(f"⚠️  TicketRouter получил не-тикетный callback: {callback_data}")
                return
            
            # Маршрутизация по action
            
            # Главное меню
            if action == "menu":
                await self.ticket_handler.handle_menu(update, context)
                return
            
            # Создание тикета
            if action == "create":
                if params and params[0] == "start":
                    await self.ticket_handler.handle_create_start(update, context)
                return
            
            # Выбор категории
            if action == "cat":
                await self.ticket_handler.handle_category_selected(update, context)
                return
            
            # Выбор приоритета
            if action == "pri":
                await self.ticket_handler.handle_priority_selected(update, context)
                return
            
            # Подтверждение
            if action == "confirm":
                await self.ticket_handler.handle_confirm(update, context)
                return
            
            # Отмена
            if action == "cancel":
                await self.ticket_handler.handle_cancel(update, context)
                return
            
            # Список тикетов
            if action == "my":
                if params and params[0] == "list":
                    await self.ticket_handler.handle_my_list(update, context)
                return
            
            # Просмотр тикета
            if action == "view":
                await self.ticket_handler.handle_view(update, context)
                return
            
            # Закрыть тикет
            if action == "close":
                await self.ticket_handler.handle_close(update, context)
                return
            
            # Неизвестное действие
            logger.warning(f"⚠️  Неизвестное тикетное действие: {action}")
            await query.answer("❌ Неизвестная команда", show_alert=True)
        
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга callback: {e}")
            await query.answer("❌ Ошибка обработки", show_alert=True)
        
        except Exception as e:
            logger.error(f"❌ Ошибка в TicketRouter: {e}", exc_info=True)
            await query.answer("❌ Произошла ошибка", show_alert=True)
    
    def get_message_handler(self) -> MessageHandler:
        """
        Получить MessageHandler для обработки текстовых сообщений
        (для шага ввода текста тикета)
        
        Returns:
            MessageHandler
        """
        return MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.ticket_handler.handle_message_received
        )
