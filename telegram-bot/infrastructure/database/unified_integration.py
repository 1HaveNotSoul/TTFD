"""
Unified Integration - Интеграция с Unified Database для Telegram Bot
Обёртка для работы с unified_users через существующие сервисы
"""
import sys
import os
import logging
from typing import Optional, Dict, Any

# Добавляем путь к shared модулю
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from database_unified import get_unified_db, UnifiedDatabase
from models import UnifiedUser

logger = logging.getLogger(__name__)


class UnifiedIntegration:
    """Интеграция Telegram Bot с Unified Database"""
    
    def __init__(self):
        self.unified_db: Optional[UnifiedDatabase] = None
    
    async def connect(self):
        """Подключиться к unified database"""
        try:
            self.unified_db = await get_unified_db()
            logger.info("✅ Unified Database подключена")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Unified Database: {e}")
            raise
    
    async def disconnect(self):
        """Отключиться от unified database"""
        if self.unified_db:
            await self.unified_db.disconnect()
            logger.info("🔌 Unified Database отключена")
    
    async def get_or_create_user(self, telegram_id: str, username: str, display_name: str) -> UnifiedUser:
        """Получить или создать пользователя"""
        # Проверяем существование
        user = await self.unified_db.get_user_by_telegram(telegram_id)
        
        if not user:
            # Создаём нового
            user = await self.unified_db.create_user(
                telegram_id=telegram_id,
                username=username,
                display_name=display_name,
                primary_platform='telegram'
            )
            logger.info(f"✅ Создан новый пользователь: telegram_id={telegram_id}, unified_id={user.id}")
        
        return user
    
    async def update_xp(self, telegram_id: str, delta_xp: int) -> Dict[str, Any]:
        """Обновить XP пользователя"""
        user = await self.unified_db.get_user_by_telegram(telegram_id)
        
        if not user:
            logger.warning(f"⚠️  Пользователь не найден: telegram_id={telegram_id}")
            return {'success': False, 'error': 'User not found'}
        
        result = await self.unified_db.update_xp(user.id, delta_xp)
        
        # Создаём событие для синхронизации
        if result['success']:
            await self.unified_db.create_event(
                user_id=user.id,
                event_type='xp_change',
                source_platform='telegram',
                data={
                    'delta_xp': delta_xp,
                    'new_xp': result['xp']
                }
            )
            
            # Если повышение ранга - создаём событие
            if result['rank_up']:
                await self.unified_db.create_event(
                    user_id=user.id,
                    event_type='rank_up',
                    source_platform='telegram',
                    data={
                        'old_rank': result['old_rank'],
                        'new_rank': result['new_rank'],
                        'reward_coins': result['reward_coins']
                    }
                )
        
        return result
    
    async def update_coins(self, telegram_id: str, delta_coins: int) -> int:
        """Обновить монеты пользователя"""
        user = await self.unified_db.get_user_by_telegram(telegram_id)
        
        if not user:
            logger.warning(f"⚠️  Пользователь не найден: telegram_id={telegram_id}")
            return 0
        
        new_coins = await self.unified_db.update_coins(user.id, delta_coins)
        
        # Создаём событие для синхронизации
        await self.unified_db.create_event(
            user_id=user.id,
            event_type='coins_change',
            source_platform='telegram',
            data={
                'delta_coins': delta_coins,
                'new_coins': new_coins
            }
        )
        
        return new_coins
    
    async def record_game(self, telegram_id: str, game_type: str, won: bool, xp_earned: int):
        """Записать сыгранную игру"""
        user = await self.unified_db.get_user_by_telegram(telegram_id)
        
        if not user:
            return
        
        # Обновляем статистику игр
        async with self.unified_db.pool.acquire() as conn:
            await conn.execute("""
                UPDATE unified_users
                SET games_played = games_played + 1,
                    games_won = games_won + $1
                WHERE id = $2
            """, 1 if won else 0, user.id)
        
        # Создаём событие
        await self.unified_db.create_event(
            user_id=user.id,
            event_type='game_played',
            source_platform='telegram',
            data={
                'game_type': game_type,
                'won': won,
                'xp_earned': xp_earned
            }
        )
    
    async def get_user_stats(self, telegram_id: str) -> Optional[Dict[str, Any]]:
        """Получить статистику пользователя"""
        user = await self.unified_db.get_user_by_telegram(telegram_id)
        
        if not user:
            return None
        
        return {
            'id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'xp': user.xp,
            'coins': user.coins,
            'rank_id': user.rank_id,
            'games_played': user.games_played,
            'games_won': user.games_won,
            'daily_streak': user.daily_streak,
            'platforms': user.platforms,
            'is_linked_discord': user.is_linked_discord,
            'is_linked_website': user.is_linked_website
        }


# Глобальный экземпляр
unified_integration: Optional[UnifiedIntegration] = None


async def get_unified_integration() -> UnifiedIntegration:
    """Получить экземпляр unified integration"""
    global unified_integration
    
    if unified_integration is None:
        unified_integration = UnifiedIntegration()
        await unified_integration.connect()
    
    return unified_integration
