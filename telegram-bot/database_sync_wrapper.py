"""
Database Sync Wrapper - Обёртка для автоматической синхронизации с Unified Database
Прозрачно синхронизирует изменения баланса между локальной БД и unified database
"""
import sys
import os
import asyncio
import logging
from typing import Optional, Dict, Any

# Добавляем путь к shared модулю
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from infrastructure.database.unified_integration import get_unified_integration, UnifiedIntegration

logger = logging.getLogger(__name__)


class TelegramDatabaseSyncWrapper:
    """
    Обёртка для database с автоматической синхронизацией
    Все изменения баланса автоматически синхронизируются с unified database
    """
    
    def __init__(self, local_db):
        """
        Args:
            local_db: Локальная база данных (database.db)
        """
        self.local_db = local_db
        self.unified: Optional[UnifiedIntegration] = None
        self._sync_enabled = False
    
    async def enable_sync(self):
        """Включить синхронизацию с unified database"""
        try:
            self.unified = await get_unified_integration()
            self._sync_enabled = True
            logger.info("✅ Синхронизация баланса включена (Telegram)")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось включить синхронизацию: {e}")
            self._sync_enabled = False
    
    def disable_sync(self):
        """Отключить синхронизацию"""
        self._sync_enabled = False
        logger.info("🔌 Синхронизация баланса отключена")
    
    # ========================================================================
    # МЕТОДЫ С СИНХРОНИЗАЦИЕЙ
    # ========================================================================
    
    def get_user(self, telegram_id):
        """Получить пользователя (без изменений)"""
        return self.local_db.get_user(telegram_id)
    
    def update_user(self, telegram_id, **kwargs):
        """Обновить пользователя (без изменений)"""
        return self.local_db.update_user(telegram_id, **kwargs)
    
    def add_xp(self, telegram_id, amount):
        """Добавить XP с синхронизацией"""
        # Локальное обновление
        result = self.local_db.add_xp(telegram_id, amount)
        
        # Синхронизация с unified database
        if self._sync_enabled and self.unified:
            asyncio.create_task(self._sync_xp_change(telegram_id, amount, result))
        
        return result
    
    def add_coins(self, telegram_id, amount):
        """Добавить монеты с синхронизацией"""
        # Локальное обновление
        new_coins = self.local_db.add_coins(telegram_id, amount)
        
        # Синхронизация с unified database
        if self._sync_enabled and self.unified:
            asyncio.create_task(self._sync_coins_change(telegram_id, amount))
        
        return new_coins
    
    def remove_coins(self, telegram_id, amount):
        """Убрать монеты с синхронизацией"""
        # Локальное обновление
        success = self.local_db.remove_coins(telegram_id, amount)
        
        # Синхронизация с unified database
        if success and self._sync_enabled and self.unified:
            asyncio.create_task(self._sync_coins_change(telegram_id, -amount))
        
        return success
    
    # ========================================================================
    # МЕТОДЫ БЕЗ СИНХРОНИЗАЦИИ (прокси к локальной БД)
    # ========================================================================
    
    def can_claim_daily(self, telegram_id):
        return self.local_db.can_claim_daily(telegram_id)
    
    def claim_daily(self, telegram_id, xp_reward, coins_reward):
        result = self.local_db.claim_daily(telegram_id, xp_reward, coins_reward)
        
        # Синхронизация если успешно
        if result.get('success') and self._sync_enabled and self.unified:
            asyncio.create_task(self._sync_xp_change(telegram_id, xp_reward, {}))
            asyncio.create_task(self._sync_coins_change(telegram_id, coins_reward))
        
        return result
    
    def get_leaderboard(self, limit=10):
        return self.local_db.get_leaderboard(limit)
    
    def get_all_users(self):
        return self.local_db.get_all_users()
    
    def link_discord(self, telegram_id, discord_id):
        return self.local_db.link_discord(telegram_id, discord_id)
    
    def get_rank_info(self, rank_id):
        return self.local_db.get_rank_info(rank_id)
    
    # ========================================================================
    # ВНУТРЕННИЕ МЕТОДЫ СИНХРОНИЗАЦИИ
    # ========================================================================
    
    async def _sync_xp_change(self, telegram_id: str, delta_xp: int, result: Dict[str, Any]):
        """Синхронизировать изменение XP"""
        try:
            await self.unified.update_xp(telegram_id, delta_xp)
            logger.info(f"✅ XP синхронизирован: telegram_id={telegram_id}, delta={delta_xp}")
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации XP: {e}")
    
    async def _sync_coins_change(self, telegram_id: str, delta_coins: int):
        """Синхронизировать изменение монет"""
        try:
            await self.unified.update_coins(telegram_id, delta_coins)
            logger.info(f"✅ Монеты синхронизированы: telegram_id={telegram_id}, delta={delta_coins}")
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации монет: {e}")


# Функция для создания обёртки
def create_sync_wrapper(local_db):
    """Создать обёртку с синхронизацией"""
    wrapper = TelegramDatabaseSyncWrapper(local_db)
    
    # Пытаемся включить синхронизацию асинхронно
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(wrapper.enable_sync())
        else:
            loop.run_until_complete(wrapper.enable_sync())
    except Exception as e:
        logger.warning(f"⚠️  Синхронизация будет включена позже: {e}")
    
    return wrapper
