"""
Admin Router - маршрутизация всех admin callback
Централизованная регистрация handlers для домена ADMIN
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

from core.callbacks import CallbackBuilder, CallbackDomain
from application.handlers.admin.admin_handler import AdminHandler
from application.handlers.tickets.admin_ticket_handler import AdminTicketHandler

logger = logging.getLogger(__name__)


class AdminRouter:
    """
    Роутер для всех админских callback
    
    Обрабатывает все callback с доменом ADMIN:
    - admin:panel - главная админ-панель
    - admin:stats - статистика
    - admin:users - управление пользователями
    - admin:tickets - управление тикетами
    - admin:ticket:* - действия с тикетами
    """
    
    def __init__(
        self,
        admin_handler: AdminHandler,
        admin_ticket_handler: AdminTicketHandler
    ):
        self.admin_handler = admin_handler
        self.admin_ticket_handler = admin_ticket_handler
    
    async def route(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Маршрутизировать админский callback к нужному handler
        
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
            
            # Проверяем что это админский callback
            if domain != CallbackDomain.ADMIN.value:
                logger.warning(f"⚠️  AdminRouter получил не-админский callback: {callback_data}")
                return
            
            # Маршрутизация по action
            
            # Главная панель
            if action == "panel":
                await self.admin_handler.handle_panel(update, context)
                return
            
            # Статистика
            if action == "stats":
                await self.admin_handler.handle_stats_panel(update, context)
                return
            
            # Пользователи
            if action == "users":
                await self.admin_handler.handle_users_panel(update, context)
                return
            
            # База данных
            if action == "database":
                await self.admin_handler.handle_database_panel(update, context)
                return
            
            # Просмотр таблицы БД
            if action == "db":
                await self.admin_handler.handle_db_table_view(update, context)
                return
            
            # Тикеты
            if action == "tickets":
                await self.admin_ticket_handler.handle_panel(update, context)
                return
            
            # Действия с тикетами
            if action == "ticket":
                await self._route_ticket(update, context, params)
                return
            
            # Неизвестное действие
            logger.warning(f"⚠️  Неизвестное админское действие: {action}")
            await query.answer("❌ Неизвестная команда", show_alert=True)
        
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга callback: {e}")
            await query.answer("❌ Ошибка обработки", show_alert=True)
        
        except Exception as e:
            logger.error(f"❌ Ошибка в AdminRouter: {e}", exc_info=True)
            await query.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _route_ticket(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        params: list[str]
    ):
        """Маршрутизация для действий с тикетами"""
        if not params:
            logger.warning("⚠️  Admin ticket callback без параметров")
            return
        
        sub_action = params[0]
        
        # admin:ticket:list:open
        if sub_action == "list":
            await self.admin_ticket_handler.handle_list(update, context)
        
        # admin:ticket:view:42
        elif sub_action == "view":
            await self.admin_ticket_handler.handle_view(update, context)
        
        # admin:ticket:assign:42
        elif sub_action == "assign":
            await self.admin_ticket_handler.handle_assign(update, context)
        
        # admin:ticket:close:42
        elif sub_action == "close":
            await self.admin_ticket_handler.handle_close(update, context)
        
        else:
            logger.warning(f"⚠️  Неизвестное действие admin ticket: {sub_action}")
