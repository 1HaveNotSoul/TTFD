"""
Sync Repository - работа с событиями синхронизации в БД
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging

from domain.models.sync_event import (
    SyncEvent, Transaction, SyncState,
    EventStatus, EventSource, EventType
)

logger = logging.getLogger(__name__)


class SyncRepository:
    """Репозиторий для работы с синхронизацией"""
    
    def __init__(self, pool):
        self.pool = pool
    
    # ========================================================================
    # СОБЫТИЯ
    # ========================================================================
    
    async def create_event(
        self,
        idempotency_key: str,
        source: str,
        event_type: str,
        user_id: int,
        payload: Dict[str, Any]
    ) -> SyncEvent:
        """
        Создать событие синхронизации
        
        Args:
            idempotency_key: Ключ идемпотентности
            source: telegram или discord
            event_type: Тип события
            user_id: ID пользователя (telegram_user_id)
            payload: Данные события
        
        Returns:
            SyncEvent
        """
        async with self.pool.acquire() as conn:
            # Проверяем существование
            existing = await conn.fetchrow(
                """
                SELECT * FROM sync_events
                WHERE idempotency_key = $1
                """,
                idempotency_key
            )
            
            if existing:
                logger.info(
                    f"🔄 Событие уже существует: {idempotency_key}"
                )
                return SyncEvent.from_db_row(existing)
            
            # Создаём новое
            row = await conn.fetchrow(
                """
                INSERT INTO sync_events (
                    id, idempotency_key, source, event_type,
                    user_id, payload, status, retries
                )
                VALUES ($1, $2, $3, $4, $5, $6, 'pending', 0)
                RETURNING *
                """,
                uuid.uuid4(), idempotency_key, source, event_type,
                user_id, payload
            )
            
            logger.info(
                f"✅ Событие создано: {event_type} для user={user_id}, "
                f"source={source}"
            )
            
            return SyncEvent.from_db_row(row)
    
    async def get_event_by_id(self, event_id: str) -> Optional[SyncEvent]:
        """Получить событие по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM sync_events
                WHERE id = $1
                """,
                uuid.UUID(event_id)
            )
            
            return SyncEvent.from_db_row(row) if row else None
    
    async def get_event_by_idempotency_key(
        self,
        idempotency_key: str
    ) -> Optional[SyncEvent]:
        """Получить событие по ключу идемпотентности"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM sync_events
                WHERE idempotency_key = $1
                """,
                idempotency_key
            )
            
            return SyncEvent.from_db_row(row) if row else None
    
    async def get_pending_events(
        self,
        limit: int = 100
    ) -> List[SyncEvent]:
        """
        Получить события ожидающие обработки
        
        Args:
            limit: Максимальное количество
        
        Returns:
            Список событий
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM sync_events
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT $1
                """,
                limit
            )
            
            return [SyncEvent.from_db_row(row) for row in rows]
    
    async def mark_event_processing(self, event_id: str):
        """Отметить событие как обрабатываемое"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sync_events
                SET status = 'processing'
                WHERE id = $1
                """,
                uuid.UUID(event_id)
            )
    
    async def mark_event_completed(
        self,
        event_id: str,
        processed_by: str
    ):
        """
        Отметить событие как завершённое
        
        Args:
            event_id: ID события
            processed_by: Кто обработал (telegram, discord, both)
        """
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sync_events
                SET status = 'completed',
                    processed_by = $2,
                    processed_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                uuid.UUID(event_id), processed_by
            )
    
    async def mark_event_failed(
        self,
        event_id: str,
        error_message: str
    ):
        """Отметить событие как провалившееся"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sync_events
                SET status = 'failed',
                    error_message = $2,
                    retries = retries + 1
                WHERE id = $1
                """,
                uuid.UUID(event_id), error_message
            )
    
    async def retry_event(self, event_id: str):
        """Повторить обработку события"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sync_events
                SET status = 'pending',
                    error_message = NULL
                WHERE id = $1 AND retries < 3
                """,
                uuid.UUID(event_id)
            )
    
    async def get_user_events(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[SyncEvent]:
        """Получить события пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM sync_events
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id, limit
            )
            
            return [SyncEvent.from_db_row(row) for row in rows]
    
    # ========================================================================
    # ТРАНЗАКЦИИ
    # ========================================================================
    
    async def create_transaction(
        self,
        idempotency_key: str,
        user_id: int,
        source: str,
        type: str,
        delta_xp: int,
        delta_balance: int,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Transaction:
        """
        Создать транзакцию
        
        Args:
            idempotency_key: Ключ идемпотентности
            user_id: ID пользователя
            source: telegram или discord
            type: xp, balance, achievement, reward
            delta_xp: Изменение XP
            delta_balance: Изменение баланса
            reason: Причина
            metadata: Дополнительные данные
        
        Returns:
            Transaction
        """
        async with self.pool.acquire() as conn:
            # Проверяем существование
            existing = await conn.fetchrow(
                """
                SELECT * FROM transactions
                WHERE idempotency_key = $1
                """,
                idempotency_key
            )
            
            if existing:
                return Transaction.from_db_row(existing)
            
            # Создаём новую
            row = await conn.fetchrow(
                """
                INSERT INTO transactions (
                    idempotency_key, user_id, source, type,
                    delta_xp, delta_balance, reason, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING *
                """,
                idempotency_key, user_id, source, type,
                delta_xp, delta_balance, reason, metadata
            )
            
            return Transaction.from_db_row(row)
    
    async def get_user_transactions(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[Transaction]:
        """Получить транзакции пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM transactions
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id, limit
            )
            
            return [Transaction.from_db_row(row) for row in rows]
    
    # ========================================================================
    # СОСТОЯНИЕ СИНХРОНИЗАЦИИ
    # ========================================================================
    
    async def get_sync_state(self, user_id: int) -> Optional[SyncState]:
        """Получить состояние синхронизации пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM sync_state
                WHERE user_id = $1
                """,
                user_id
            )
            
            return SyncState.from_db_row(row) if row else None
    
    async def upsert_sync_state(
        self,
        user_id: int,
        telegram_xp: Optional[int] = None,
        telegram_balance: Optional[int] = None,
        telegram_rank: Optional[int] = None,
        discord_xp: Optional[int] = None,
        discord_balance: Optional[int] = None,
        discord_rank: Optional[int] = None
    ) -> SyncState:
        """
        Обновить или создать состояние синхронизации
        
        Args:
            user_id: ID пользователя
            telegram_xp: XP в Telegram (если нужно обновить)
            telegram_balance: Баланс в Telegram
            telegram_rank: Ранг в Telegram
            discord_xp: XP в Discord
            discord_balance: Баланс в Discord
            discord_rank: Ранг в Discord
        
        Returns:
            SyncState
        """
        async with self.pool.acquire() as conn:
            # Получаем текущее состояние
            current = await self.get_sync_state(user_id)
            
            if not current:
                # Создаём новое
                row = await conn.fetchrow(
                    """
                    INSERT INTO sync_state (
                        user_id,
                        last_telegram_xp, last_telegram_balance, last_telegram_rank,
                        last_discord_xp, last_discord_balance, last_discord_rank
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING *
                    """,
                    user_id,
                    telegram_xp or 0, telegram_balance or 0, telegram_rank or 1,
                    discord_xp or 0, discord_balance or 0, discord_rank or 1
                )
            else:
                # Обновляем существующее
                updates = []
                params = [user_id]
                param_idx = 2
                
                if telegram_xp is not None:
                    updates.append(f"last_telegram_xp = ${param_idx}")
                    params.append(telegram_xp)
                    param_idx += 1
                
                if telegram_balance is not None:
                    updates.append(f"last_telegram_balance = ${param_idx}")
                    params.append(telegram_balance)
                    param_idx += 1
                
                if telegram_rank is not None:
                    updates.append(f"last_telegram_rank = ${param_idx}")
                    params.append(telegram_rank)
                    param_idx += 1
                
                if discord_xp is not None:
                    updates.append(f"last_discord_xp = ${param_idx}")
                    params.append(discord_xp)
                    param_idx += 1
                
                if discord_balance is not None:
                    updates.append(f"last_discord_balance = ${param_idx}")
                    params.append(discord_balance)
                    param_idx += 1
                
                if discord_rank is not None:
                    updates.append(f"last_discord_rank = ${param_idx}")
                    params.append(discord_rank)
                    param_idx += 1
                
                if not updates:
                    return current
                
                query = f"""
                    UPDATE sync_state
                    SET {', '.join(updates)}
                    WHERE user_id = $1
                    RETURNING *
                """
                
                row = await conn.fetchrow(query, *params)
            
            return SyncState.from_db_row(row)
    
    async def update_reconcile_time(self, user_id: int):
        """Обновить время последнего reconcile"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sync_state
                SET last_reconcile_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                """,
                user_id
            )
    
    async def increment_reconcile_errors(self, user_id: int):
        """Увеличить счётчик ошибок reconcile"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sync_state
                SET reconcile_errors = reconcile_errors + 1
                WHERE user_id = $1
                """,
                user_id
            )
    
    async def get_users_needing_reconcile(
        self,
        hours_since_last: int = 1,
        limit: int = 100
    ) -> List[int]:
        """
        Получить пользователей которым нужен reconcile
        
        Args:
            hours_since_last: Часов с последнего reconcile
            limit: Максимальное количество
        
        Returns:
            Список user_id
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id FROM sync_state
                WHERE last_reconcile_at IS NULL
                    OR last_reconcile_at < CURRENT_TIMESTAMP - INTERVAL '1 hour' * $1
                ORDER BY last_reconcile_at ASC NULLS FIRST
                LIMIT $2
                """,
                hours_since_last, limit
            )
            
            return [row['user_id'] for row in rows]
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    async def cleanup_old_events(self, days: int = 30):
        """
        Очистить старые события
        
        Args:
            days: Удалить события старше N дней
        """
        async with self.pool.acquire() as conn:
            # Удаляем завершённые события старше 30 дней
            result1 = await conn.execute(
                """
                DELETE FROM sync_events
                WHERE status = 'completed'
                    AND created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * $1
                """,
                days
            )
            
            # Удаляем провалившиеся события старше 7 дней
            result2 = await conn.execute(
                """
                DELETE FROM sync_events
                WHERE status = 'failed'
                    AND retries >= 3
                    AND created_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
                """
            )
            
            count1 = int(result1.split()[-1]) if result1 else 0
            count2 = int(result2.split()[-1]) if result2 else 0
            
            if count1 + count2 > 0:
                logger.info(
                    f"🧹 Очищено событий: {count1} завершённых, "
                    f"{count2} провалившихся"
                )
    
    async def get_stats(self) -> Dict[str, int]:
        """Получить статистику синхронизации"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) as total
                FROM sync_events
                """
            )
            
            return dict(stats)
