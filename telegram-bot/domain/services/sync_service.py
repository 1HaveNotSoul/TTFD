"""
Sync Service - бизнес-логика двусторонней синхронизации
"""
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from domain.models.sync_event import (
    SyncEvent, EventSource, EventType, EventStatus,
    generate_idempotency_key
)
from domain.models.user import calculate_rank_by_xp
from infrastructure.database.repositories.sync_repository import SyncRepository
from infrastructure.database.repositories.user_repository import UserRepository
from infrastructure.database.repositories.discord_repository import DiscordRepository

logger = logging.getLogger(__name__)


class SyncService:
    """Сервис для двусторонней синхронизации Telegram ↔ Discord"""
    
    def __init__(
        self,
        sync_repo: SyncRepository,
        user_repo: UserRepository,
        discord_repo: DiscordRepository
    ):
        self.sync_repo = sync_repo
        self.user_repo = user_repo
        self.discord_repo = discord_repo
    
    # ========================================================================
    # СОЗДАНИЕ СОБЫТИЙ
    # ========================================================================
    
    async def create_xp_change_event(
        self,
        user_id: int,
        delta_xp: int,
        source: str,
        reason: str,
        entity_id: Optional[str] = None
    ) -> SyncEvent:
        """
        Создать событие изменения XP
        
        Args:
            user_id: ID пользователя (telegram_user_id)
            delta_xp: Изменение XP
            source: telegram или discord
            reason: Причина (game, daily, voice_chat, etc)
            entity_id: ID сущности (game_id, session_id, etc)
        
        Returns:
            SyncEvent
        """
        # Генерируем ключ идемпотентности
        entity_id = entity_id or f"{reason}_{int(datetime.now().timestamp())}"
        idempotency_key = generate_idempotency_key(
            source=source,
            event_type="xp_change",
            entity_id=entity_id,
            user_id=user_id
        )
        
        # Создаём событие
        event = await self.sync_repo.create_event(
            idempotency_key=idempotency_key,
            source=source,
            event_type=EventType.XP_CHANGE.value,
            user_id=user_id,
            payload={
                'delta_xp': delta_xp,
                'reason': reason,
                'entity_id': entity_id
            }
        )
        
        # Создаём транзакцию для аудита
        await self.sync_repo.create_transaction(
            idempotency_key=idempotency_key,
            user_id=user_id,
            source=source,
            type='xp',
            delta_xp=delta_xp,
            delta_balance=0,
            reason=reason,
            metadata={'entity_id': entity_id}
        )
        
        logger.info(
            f"📝 Событие XP создано: user={user_id}, delta={delta_xp}, "
            f"source={source}, reason={reason}"
        )
        
        return event
    
    async def create_balance_change_event(
        self,
        user_id: int,
        delta_balance: int,
        source: str,
        reason: str,
        entity_id: Optional[str] = None
    ) -> SyncEvent:
        """
        Создать событие изменения баланса
        
        Args:
            user_id: ID пользователя
            delta_balance: Изменение баланса
            source: telegram или discord
            reason: Причина
            entity_id: ID сущности
        
        Returns:
            SyncEvent
        """
        entity_id = entity_id or f"{reason}_{int(datetime.now().timestamp())}"
        idempotency_key = generate_idempotency_key(
            source=source,
            event_type="balance_change",
            entity_id=entity_id,
            user_id=user_id
        )
        
        event = await self.sync_repo.create_event(
            idempotency_key=idempotency_key,
            source=source,
            event_type=EventType.BALANCE_CHANGE.value,
            user_id=user_id,
            payload={
                'delta_balance': delta_balance,
                'reason': reason,
                'entity_id': entity_id
            }
        )
        
        await self.sync_repo.create_transaction(
            idempotency_key=idempotency_key,
            user_id=user_id,
            source=source,
            type='balance',
            delta_xp=0,
            delta_balance=delta_balance,
            reason=reason,
            metadata={'entity_id': entity_id}
        )
        
        logger.info(
            f"📝 Событие баланса создано: user={user_id}, "
            f"delta={delta_balance}, source={source}"
        )
        
        return event
    
    async def create_rank_change_event(
        self,
        user_id: int,
        old_rank: int,
        new_rank: int,
        source: str
    ) -> SyncEvent:
        """
        Создать событие изменения ранга
        
        Args:
            user_id: ID пользователя
            old_rank: Старый ранг
            new_rank: Новый ранг
            source: telegram или discord
        
        Returns:
            SyncEvent
        """
        entity_id = f"rank_{old_rank}_to_{new_rank}"
        idempotency_key = generate_idempotency_key(
            source=source,
            event_type="rank_change",
            entity_id=entity_id,
            user_id=user_id,
            timestamp=int(datetime.now().timestamp())
        )
        
        event = await self.sync_repo.create_event(
            idempotency_key=idempotency_key,
            source=source,
            event_type=EventType.RANK_CHANGE.value,
            user_id=user_id,
            payload={
                'old_rank': old_rank,
                'new_rank': new_rank
            }
        )
        
        logger.info(
            f"📝 Событие ранга создано: user={user_id}, "
            f"{old_rank} → {new_rank}, source={source}"
        )
        
        return event
    
    async def create_achievement_event(
        self,
        user_id: int,
        achievement_id: str,
        source: str
    ) -> SyncEvent:
        """
        Создать событие получения достижения
        
        Args:
            user_id: ID пользователя
            achievement_id: ID достижения
            source: telegram или discord
        
        Returns:
            SyncEvent
        """
        idempotency_key = generate_idempotency_key(
            source=source,
            event_type="achievement_unlock",
            entity_id=achievement_id,
            user_id=user_id
        )
        
        event = await self.sync_repo.create_event(
            idempotency_key=idempotency_key,
            source=source,
            event_type=EventType.ACHIEVEMENT_UNLOCK.value,
            user_id=user_id,
            payload={
                'achievement_id': achievement_id
            }
        )
        
        logger.info(
            f"📝 Событие достижения создано: user={user_id}, "
            f"achievement={achievement_id}, source={source}"
        )
        
        return event
    
    # ========================================================================
    # ОБРАБОТКА СОБЫТИЙ
    # ========================================================================
    
    async def process_event(self, event: SyncEvent) -> bool:
        """
        Обработать событие синхронизации
        
        Args:
            event: Событие для обработки
        
        Returns:
            True если успешно
        """
        try:
            # Отмечаем как обрабатываемое
            await self.sync_repo.mark_event_processing(event.id)
            
            # Проверяем привязку Discord
            link = await self.discord_repo.get_active_link(event.user_id)
            
            if not link or not link.discord_user_id:
                logger.warning(
                    f"⚠️  Нет привязки Discord для user={event.user_id}, "
                    f"пропускаем событие"
                )
                await self.sync_repo.mark_event_completed(
                    event.id,
                    processed_by=event.source
                )
                return True
            
            # Обрабатываем в зависимости от типа
            if event.event_type == EventType.XP_CHANGE.value:
                success = await self._process_xp_change(event, link)
            
            elif event.event_type == EventType.BALANCE_CHANGE.value:
                success = await self._process_balance_change(event, link)
            
            elif event.event_type == EventType.RANK_CHANGE.value:
                success = await self._process_rank_change(event, link)
            
            elif event.event_type == EventType.ACHIEVEMENT_UNLOCK.value:
                success = await self._process_achievement(event, link)
            
            else:
                logger.warning(f"⚠️  Неизвестный тип события: {event.event_type}")
                success = False
            
            if success:
                # Определяем кто обработал
                if event.source == EventSource.TELEGRAM.value:
                    processed_by = "discord"
                else:
                    processed_by = "telegram"
                
                await self.sync_repo.mark_event_completed(event.id, processed_by)
                logger.info(f"✅ Событие обработано: {event.id}")
            else:
                await self.sync_repo.mark_event_failed(
                    event.id,
                    "Не удалось обработать событие"
                )
            
            return success
        
        except Exception as e:
            logger.error(f"❌ Ошибка обработки события {event.id}: {e}")
            await self.sync_repo.mark_event_failed(event.id, str(e))
            return False
    
    async def _process_xp_change(self, event: SyncEvent, link) -> bool:
        """Обработать изменение XP"""
        delta_xp = event.payload.get('delta_xp', 0)
        
        if event.source == EventSource.TELEGRAM.value:
            # Telegram → Discord: обновляем Discord
            # TODO: Здесь будет вызов Discord Bot API для обновления XP
            logger.info(
                f"🔄 TG→DS: XP изменение user={event.user_id}, delta={delta_xp}"
            )
            
            # Обновляем sync_state
            user = await self.user_repo.get_by_id(event.user_id)
            await self.sync_repo.upsert_sync_state(
                user_id=event.user_id,
                telegram_xp=user.xp,
                discord_xp=user.xp  # Синхронизируем
            )
        
        else:
            # Discord → Telegram: обновляем Telegram
            await self.user_repo.update_xp(event.user_id, delta_xp)
            
            logger.info(
                f"🔄 DS→TG: XP изменение user={event.user_id}, delta={delta_xp}"
            )
            
            # Проверяем изменение ранга
            user = await self.user_repo.get_by_id(event.user_id)
            new_rank = calculate_rank_by_xp(user.xp)
            
            if new_rank.id != user.rank_id:
                # Создаём событие изменения ранга
                await self.create_rank_change_event(
                    user_id=event.user_id,
                    old_rank=user.rank_id,
                    new_rank=new_rank.id,
                    source=EventSource.DISCORD.value
                )
                
                # Обновляем ранг
                await self.user_repo.update_rank(event.user_id, new_rank.id)
            
            # Обновляем sync_state
            await self.sync_repo.upsert_sync_state(
                user_id=event.user_id,
                telegram_xp=user.xp,
                discord_xp=user.xp
            )
        
        return True
    
    async def _process_balance_change(self, event: SyncEvent, link) -> bool:
        """Обработать изменение баланса"""
        delta_balance = event.payload.get('delta_balance', 0)
        
        if event.source == EventSource.TELEGRAM.value:
            # Telegram → Discord
            logger.info(
                f"🔄 TG→DS: Баланс изменение user={event.user_id}, "
                f"delta={delta_balance}"
            )
            
            user = await self.user_repo.get_by_id(event.user_id)
            await self.sync_repo.upsert_sync_state(
                user_id=event.user_id,
                telegram_balance=user.coins,
                discord_balance=user.coins
            )
        
        else:
            # Discord → Telegram
            await self.user_repo.update_coins(event.user_id, delta_balance)
            
            logger.info(
                f"🔄 DS→TG: Баланс изменение user={event.user_id}, "
                f"delta={delta_balance}"
            )
            
            user = await self.user_repo.get_by_id(event.user_id)
            await self.sync_repo.upsert_sync_state(
                user_id=event.user_id,
                telegram_balance=user.coins,
                discord_balance=user.coins
            )
        
        return True
    
    async def _process_rank_change(self, event: SyncEvent, link) -> bool:
        """Обработать изменение ранга"""
        old_rank = event.payload.get('old_rank')
        new_rank = event.payload.get('new_rank')
        
        if event.source == EventSource.TELEGRAM.value:
            # Telegram → Discord: обновляем Discord роль
            # TODO: Здесь будет вызов Discord Bot для смены роли
            logger.info(
                f"🔄 TG→DS: Ранг изменение user={event.user_id}, "
                f"{old_rank} → {new_rank}"
            )
            
            await self.sync_repo.upsert_sync_state(
                user_id=event.user_id,
                telegram_rank=new_rank,
                discord_rank=new_rank
            )
        
        else:
            # Discord → Telegram: игнорируем (rank-derived стратегия)
            logger.warning(
                f"⚠️  DS→TG: Ранг изменение игнорируется (rank-derived), "
                f"user={event.user_id}"
            )
        
        return True
    
    async def _process_achievement(self, event: SyncEvent, link) -> bool:
        """Обработать получение достижения"""
        achievement_id = event.payload.get('achievement_id')
        
        if event.source == EventSource.TELEGRAM.value:
            # Telegram → Discord: выдаём Discord роль
            # TODO: Здесь будет вызов Discord Bot для выдачи роли
            logger.info(
                f"🔄 TG→DS: Достижение user={event.user_id}, "
                f"achievement={achievement_id}"
            )
        
        else:
            # Discord → Telegram: добавляем достижение
            # TODO: Интеграция с AchievementService
            logger.info(
                f"🔄 DS→TG: Достижение user={event.user_id}, "
                f"achievement={achievement_id}"
            )
        
        return True
    
    # ========================================================================
    # RECONCILE
    # ========================================================================
    
    async def reconcile_user(self, user_id: int) -> Dict[str, Any]:
        """
        Проверить и исправить расхождения для пользователя
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Словарь с результатами reconcile
        """
        try:
            # Получаем данные
            user = await self.user_repo.get_by_id(user_id)
            sync_state = await self.sync_repo.get_sync_state(user_id)
            link = await self.discord_repo.get_active_link(user_id)
            
            if not link or not link.discord_user_id:
                return {'status': 'no_link', 'user_id': user_id}
            
            if not sync_state:
                # Создаём начальное состояние
                await self.sync_repo.upsert_sync_state(
                    user_id=user_id,
                    telegram_xp=user.xp,
                    telegram_balance=user.coins,
                    telegram_rank=user.rank_id,
                    discord_xp=user.xp,
                    discord_balance=user.coins,
                    discord_rank=user.rank_id
                )
                
                await self.sync_repo.update_reconcile_time(user_id)
                
                return {
                    'status': 'initialized',
                    'user_id': user_id
                }
            
            # Проверяем расхождения
            issues = []
            
            # XP
            if sync_state.has_xp_diff:
                issues.append({
                    'type': 'xp',
                    'telegram': sync_state.last_telegram_xp,
                    'discord': sync_state.last_discord_xp,
                    'diff': sync_state.last_telegram_xp - sync_state.last_discord_xp
                })
                
                # Источник истины - Telegram
                # TODO: Синхронизировать в Discord
                await self.sync_repo.upsert_sync_state(
                    user_id=user_id,
                    discord_xp=user.xp
                )
            
            # Баланс
            if sync_state.has_balance_diff:
                issues.append({
                    'type': 'balance',
                    'telegram': sync_state.last_telegram_balance,
                    'discord': sync_state.last_discord_balance,
                    'diff': sync_state.last_telegram_balance - sync_state.last_discord_balance
                })
                
                await self.sync_repo.upsert_sync_state(
                    user_id=user_id,
                    discord_balance=user.coins
                )
            
            # Ранг
            if sync_state.has_rank_diff:
                issues.append({
                    'type': 'rank',
                    'telegram': sync_state.last_telegram_rank,
                    'discord': sync_state.last_discord_rank
                })
                
                await self.sync_repo.upsert_sync_state(
                    user_id=user_id,
                    discord_rank=user.rank_id
                )
            
            # Обновляем время reconcile
            await self.sync_repo.update_reconcile_time(user_id)
            
            if issues:
                logger.warning(
                    f"⚠️  Reconcile: найдены расхождения для user={user_id}, "
                    f"issues={len(issues)}"
                )
            
            return {
                'status': 'completed',
                'user_id': user_id,
                'issues': issues
            }
        
        except Exception as e:
            logger.error(f"❌ Ошибка reconcile для user={user_id}: {e}")
            await self.sync_repo.increment_reconcile_errors(user_id)
            
            return {
                'status': 'error',
                'user_id': user_id,
                'error': str(e)
            }
    
    async def reconcile_all_users(self, limit: int = 100) -> Dict[str, Any]:
        """
        Запустить reconcile для всех пользователей
        
        Args:
            limit: Максимальное количество пользователей
        
        Returns:
            Статистика reconcile
        """
        user_ids = await self.sync_repo.get_users_needing_reconcile(
            hours_since_last=1,
            limit=limit
        )
        
        if not user_ids:
            return {
                'status': 'no_users',
                'processed': 0
            }
        
        logger.info(f"🔄 Reconcile: обработка {len(user_ids)} пользователей")
        
        results = {
            'completed': 0,
            'errors': 0,
            'issues_found': 0
        }
        
        for user_id in user_ids:
            result = await self.reconcile_user(user_id)
            
            if result['status'] == 'completed':
                results['completed'] += 1
                if result.get('issues'):
                    results['issues_found'] += len(result['issues'])
            elif result['status'] == 'error':
                results['errors'] += 1
        
        logger.info(
            f"✅ Reconcile завершён: {results['completed']} пользователей, "
            f"{results['issues_found']} расхождений исправлено, "
            f"{results['errors']} ошибок"
        )
        
        return results
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику синхронизации"""
        return await self.sync_repo.get_stats()
