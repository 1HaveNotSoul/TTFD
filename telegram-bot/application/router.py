"""
Centralized callback router
Единая точка маршрутизации всех callback
"""
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from typing import Callable, Dict, Optional
import logging

from core.callbacks import CallbackBuilder, CallbackDomain

logger = logging.getLogger(__name__)


class CallbackRouter:
    """
    Централизованный роутер для callback handlers
    
    Преимущества:
    - Единая точка регистрации
    - Автоматическая валидация callback_data
    - Логирование всех callback
    - Защита от дублирования
    """
    
    def __init__(self):
        self._routes: Dict[str, Callable] = {}
        self._domain_handlers: Dict[str, Callable] = {}
    
    def register_exact(
        self,
        callback_data: str,
        handler: Callable
    ):
        """
        Зарегистрировать точный callback
        
        Args:
            callback_data: Точная строка callback
            handler: Async функция-обработчик
        """
        if callback_data in self._routes:
            logger.warning(f"⚠️  Перезапись callback: {callback_data}")
        
        self._routes[callback_data] = handler
        logger.debug(f"✅ Зарегистрирован callback: {callback_data}")
    
    def register_domain(
        self,
        domain: CallbackDomain,
        handler: Callable
    ):
        """
        Зарегистрировать обработчик для всего домена
        
        Args:
            domain: Домен (GAME, TICKET, etc.)
            handler: Async функция-обработчик
        """
        domain_key = domain.value
        
        if domain_key in self._domain_handlers:
            logger.warning(f"⚠️  Перезапись домена: {domain_key}")
        
        self._domain_handlers[domain_key] = handler
        logger.debug(f"✅ Зарегистрирован домен: {domain_key}")
    
    async def route(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Маршрутизировать callback к нужному обработчику
        
        Args:
            update: Telegram Update
            context: Telegram Context
        """
        query = update.callback_query
        
        if not query:
            return
        
        callback_data = query.data
        
        # Логируем callback
        user = query.from_user
        logger.info(
            f"📞 Callback: {callback_data} "
            f"от {user.first_name} ({user.id})"
        )
        
        # 1. Проверяем точное совпадение
        if callback_data in self._routes:
            handler = self._routes[callback_data]
            try:
                await handler(update, context)
                return
            except Exception as e:
                logger.error(f"❌ Ошибка в handler {callback_data}: {e}")
                await query.answer("❌ Произошла ошибка", show_alert=True)
                return
        
        # 2. Проверяем домен
        try:
            domain, action, params = CallbackBuilder.parse(callback_data)
            
            if domain in self._domain_handlers:
                handler = self._domain_handlers[domain]
                try:
                    await handler(update, context)
                    return
                except Exception as e:
                    logger.error(f"❌ Ошибка в domain handler {domain}: {e}")
                    await query.answer("❌ Произошла ошибка", show_alert=True)
                    return
        
        except ValueError:
            pass
        
        # 3. Callback не найден
        logger.warning(f"⚠️  Неизвестный callback: {callback_data}")
        await query.answer("❌ Неизвестная команда", show_alert=True)
    
    def get_handler(self) -> CallbackQueryHandler:
        """
        Получить CallbackQueryHandler для регистрации в Application
        
        Returns:
            CallbackQueryHandler
        """
        return CallbackQueryHandler(self.route)
    
    def get_stats(self) -> dict:
        """Получить статистику роутера"""
        return {
            'exact_routes': len(self._routes),
            'domain_handlers': len(self._domain_handlers),
            'total': len(self._routes) + len(self._domain_handlers)
        }


# Глобальный экземпляр роутера
callback_router = CallbackRouter()
