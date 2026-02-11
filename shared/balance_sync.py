"""
Balance Sync - Автоматическая синхронизация баланса между платформами
Обеспечивает единый баланс монет для Telegram, Discord и Website
"""
import asyncio
import logging
from typing import Optional
from database_unified import get_unified_db, UnifiedDatabase

logger = logging.getLogger(__name__)


class BalanceSync:
    """Синхронизация баланса между платформами"""
    
    def __init__(self):
        self.unified_db: Optional[UnifiedDatabase] = None
        self.running = False
    
    async def start(self):
        """Запустить синхронизацию"""
        self.unified_db = await get_unified_db()
        self.running = True
        logger.info("✅ Balance Sync запущен")
        
        # Запускаем фоновую задачу
        asyncio.create_task(self._sync_loop())
    
    async def stop(self):
        """Остановить синхронизацию"""
        self.running = False
        logger.info("🔌 Balance Sync остановлен")
    
    async def _sync_loop(self):
        """Основной цикл синхронизации"""
        while self.running:
            try:
                await self._process_pending_events()
                await asyncio.sleep(5)  # Проверяем каждые 5 секунд
            except Exception as e:
                logger.error(f"❌ Ошибка синхронизации: {e}")
                await asyncio.sleep(10)
    
    async def _process_pending_events(self):
        """Обработать необработанные события"""
        events = await self.unified_db.get_pending_events(limit=50)
        
        for event in events:
            try:
                # Обрабатываем только события изменения баланса
                if event.event_type == 'coins_change':
                    await self._sync_coins_change(event)
                elif event.event_type == 'xp_change':
                    await self._sync_xp_change(event)
                elif event.event_type == 'rank_up':
                    await self._sync_rank_up(event)
                
                # Отмечаем как обработанное
                await self.unified_db.mark_event_processed(event.id)
                
            except Exception as e:
                logger.error(f"❌ Ошибка обработки события {event.id}: {e}")
    
    async def _sync_coins_change(self, event):
        """Синхронизировать изменение монет"""
        user = await self.unified_db.get_user_by_id(event.user_id)
        
        if not user:
            return
        
        logger.info(f"💰 Синхронизация монет: user_id={user.id}, "
                   f"source={event.source_platform}, "
                   f"delta={event.data.get('delta_coins')}, "
                   f"new_coins={event.data.get('new_coins')}")
        
        # Монеты уже обновлены в unified_users, событие просто для логирования
    
    async def _sync_xp_change(self, event):
        """Синхронизировать изменение XP"""
        user = await self.unified_db.get_user_by_id(event.user_id)
        
        if not user:
            return
        
        logger.info(f"⭐ Синхронизация XP: user_id={user.id}, "
                   f"source={event.source_platform}, "
                   f"delta={event.data.get('delta_xp')}, "
                   f"new_xp={event.data.get('new_xp')}")
    
    async def _sync_rank_up(self, event):
        """Синхронизировать повышение ранга"""
        user = await self.unified_db.get_user_by_id(event.user_id)
        
        if not user:
            return
        
        logger.info(f"🎉 Синхронизация ранга: user_id={user.id}, "
                   f"source={event.source_platform}, "
                   f"old_rank={event.data.get('old_rank')}, "
                   f"new_rank={event.data.get('new_rank')}, "
                   f"reward={event.data.get('reward_coins')}")


# Глобальный экземпляр
balance_sync: Optional[BalanceSync] = None


async def get_balance_sync() -> BalanceSync:
    """Получить экземпляр balance sync"""
    global balance_sync
    
    if balance_sync is None:
        balance_sync = BalanceSync()
        await balance_sync.start()
    
    return balance_sync
