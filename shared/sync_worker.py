"""
Sync Worker - Воркер для синхронизации событий между платформами
Обрабатывает события из cross_platform_events и применяет изменения
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from database_unified import get_unified_db
from models import CrossPlatformEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncWorker:
    """Воркер для обработки событий синхронизации"""
    
    def __init__(self):
        self.unified_db = None
        self.running = False
    
    async def start(self):
        """Запустить воркер"""
        logger.info("🔄 Запуск Sync Worker...")
        
        self.unified_db = await get_unified_db()
        self.running = True
        
        # Запускаем фоновую задачу
        asyncio.create_task(self._process_events_loop())
        
        logger.info("✅ Sync Worker запущен")
    
    async def stop(self):
        """Остановить воркер"""
        logger.info("🛑 Остановка Sync Worker...")
        self.running = False
        
        if self.unified_db:
            await self.unified_db.disconnect()
        
        logger.info("✅ Sync Worker остановлен")
    
    async def _process_events_loop(self):
        """Основной цикл обработки событий"""
        while self.running:
            try:
                await self._process_pending_events()
                await asyncio.sleep(5)  # Каждые 5 секунд
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле обработки событий: {e}")
                await asyncio.sleep(10)  # Ждём дольше при ошибке
    
    async def _process_pending_events(self):
        """Обработать необработанные события"""
        try:
            # Получаем необработанные события
            events = await self.unified_db.get_pending_events(limit=100)
            
            if not events:
                return
            
            logger.info(f"📝 Обработка {len(events)} событий...")
            
            for event in events:
                try:
                    await self._process_event(event)
                    await self.unified_db.mark_event_processed(event.id)
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки события {event.id}: {e}")
            
            logger.info(f"✅ Обработано {len(events)} событий")
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения событий: {e}")
    
    async def _process_event(self, event: CrossPlatformEvent):
        """Обработать одно событие"""
        event_type = event.event_type
        user_id = event.user_id
        source = event.source_platform
        data = event.data
        
        logger.info(f"🔄 Обработка события: {event_type} от {source} для user_id={user_id}")
        
        # Обработка разных типов событий
        if event_type == 'xp_change':
            await self._handle_xp_change(user_id, data, source)
        
        elif event_type == 'coins_change':
            await self._handle_coins_change(user_id, data, source)
        
        elif event_type == 'rank_up':
            await self._handle_rank_up(user_id, data, source)
        
        elif event_type == 'achievement_unlock':
            await self._handle_achievement_unlock(user_id, data, source)
        
        elif event_type == 'game_played':
            await self._handle_game_played(user_id, data, source)
        
        elif event_type == 'voice_time':
            await self._handle_voice_time(user_id, data, source)
        
        elif event_type == 'message_sent':
            await self._handle_message_sent(user_id, data, source)
        
        else:
            logger.warning(f"⚠️  Неизвестный тип события: {event_type}")
    
    async def _handle_xp_change(self, user_id: int, data: dict, source: str):
        """Обработать изменение XP"""
        delta_xp = data.get('delta_xp', 0)
        
        if delta_xp == 0:
            return
        
        # XP уже обновлён в unified_users, просто логируем
        logger.info(f"   💎 XP изменён: {delta_xp:+d} (источник: {source})")
    
    async def _handle_coins_change(self, user_id: int, data: dict, source: str):
        """Обработать изменение монет"""
        delta_coins = data.get('delta_coins', 0)
        
        if delta_coins == 0:
            return
        
        # Монеты уже обновлены в unified_users, просто логируем
        logger.info(f"   💰 Монеты изменены: {delta_coins:+d} (источник: {source})")
    
    async def _handle_rank_up(self, user_id: int, data: dict, source: str):
        """Обработать повышение ранга"""
        old_rank = data.get('old_rank')
        new_rank = data.get('new_rank')
        reward_coins = data.get('reward_coins', 0)
        
        logger.info(f"   🎉 Повышение ранга: {old_rank} → {new_rank} (+{reward_coins} монет)")
        
        # Здесь можно добавить логику для:
        # - Отправки уведомлений на другие платформы
        # - Выдачи Discord ролей
        # - Обновления профиля на Website
    
    async def _handle_achievement_unlock(self, user_id: int, data: dict, source: str):
        """Обработать разблокировку достижения"""
        achievement_id = data.get('achievement_id')
        achievement_name = data.get('achievement_name', 'Unknown')
        
        logger.info(f"   🏅 Достижение разблокировано: {achievement_name}")
        
        # Здесь можно добавить логику для:
        # - Отправки уведомлений на другие платформы
        # - Выдачи Discord ролей за достижения
    
    async def _handle_game_played(self, user_id: int, data: dict, source: str):
        """Обработать сыгранную игру"""
        game_type = data.get('game_type', 'unknown')
        won = data.get('won', False)
        xp_earned = data.get('xp_earned', 0)
        
        logger.info(f"   🎮 Игра сыграна: {game_type} ({'победа' if won else 'поражение'}, +{xp_earned} XP)")
    
    async def _handle_voice_time(self, user_id: int, data: dict, source: str):
        """Обработать время в войсе"""
        duration = data.get('duration', 0)
        xp_earned = data.get('xp_earned', 0)
        
        logger.info(f"   🎤 Время в войсе: {duration}с (+{xp_earned} XP)")
    
    async def _handle_message_sent(self, user_id: int, data: dict, source: str):
        """Обработать отправленное сообщение"""
        xp_earned = data.get('xp_earned', 0)
        
        logger.info(f"   💬 Сообщение отправлено (+{xp_earned} XP)")


# Глобальный экземпляр
sync_worker: Optional[SyncWorker] = None


async def get_sync_worker() -> SyncWorker:
    """Получить экземпляр sync worker"""
    global sync_worker
    
    if sync_worker is None:
        sync_worker = SyncWorker()
        await sync_worker.start()
    
    return sync_worker


async def stop_sync_worker():
    """Остановить sync worker"""
    global sync_worker
    
    if sync_worker:
        await sync_worker.stop()
        sync_worker = None


# Для тестирования
if __name__ == "__main__":
    async def test():
        worker = await get_sync_worker()
        
        # Ждём 60 секунд
        await asyncio.sleep(60)
        
        await stop_sync_worker()
    
    asyncio.run(test())
