"""
Sync Event models - модели событий синхронизации
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class EventSource(Enum):
    """Источник события"""
    TELEGRAM = "telegram"
    DISCORD = "discord"


class EventType(Enum):
    """Тип события"""
    XP_CHANGE = "xp_change"
    BALANCE_CHANGE = "balance_change"
    RANK_CHANGE = "rank_change"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    REWARD_GRANT = "reward_grant"


class EventStatus(Enum):
    """Статус обработки события"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SyncEvent:
    """Модель события синхронизации"""
    id: str  # UUID
    idempotency_key: str
    
    # Источник и тип
    source: str  # telegram, discord
    event_type: str  # xp_change, balance_change, etc
    
    # Пользователь
    user_id: int  # telegram_user_id
    
    # Данные события
    payload: Dict[str, Any]
    
    # Статус обработки
    status: str  # pending, processing, completed, failed
    processed_by: Optional[str]  # telegram, discord, both
    
    # Ошибки и повторы
    retries: int
    error_message: Optional[str]
    
    # Метаданные
    created_at: datetime
    processed_at: Optional[datetime]
    
    @classmethod
    def from_db_row(cls, row):
        """Создать SyncEvent из строки БД"""
        if not row:
            return None
        
        return cls(
            id=str(row['id']),
            idempotency_key=row['idempotency_key'],
            source=row['source'],
            event_type=row['event_type'],
            user_id=row['user_id'],
            payload=row['payload'],
            status=row['status'],
            processed_by=row.get('processed_by'),
            retries=row['retries'],
            error_message=row.get('error_message'),
            created_at=row['created_at'],
            processed_at=row.get('processed_at')
        )
    
    @property
    def is_pending(self) -> bool:
        """Ожидает ли обработки"""
        return self.status == EventStatus.PENDING.value
    
    @property
    def is_completed(self) -> bool:
        """Завершено ли"""
        return self.status == EventStatus.COMPLETED.value
    
    @property
    def is_failed(self) -> bool:
        """Провалено ли"""
        return self.status == EventStatus.FAILED.value
    
    @property
    def can_retry(self) -> bool:
        """Можно ли повторить"""
        return self.is_failed and self.retries < 3


@dataclass
class Transaction:
    """Модель транзакции (для аудита)"""
    id: int
    idempotency_key: str
    
    # Пользователь
    user_id: int  # telegram_user_id
    
    # Источник и тип
    source: str  # telegram, discord
    type: str  # xp, balance, achievement, reward
    
    # Изменения
    delta_xp: int
    delta_balance: int
    
    # Причина
    reason: str
    metadata: Optional[Dict[str, Any]]
    
    # Метаданные
    created_at: datetime
    
    @classmethod
    def from_db_row(cls, row):
        """Создать Transaction из строки БД"""
        if not row:
            return None
        
        return cls(
            id=row['id'],
            idempotency_key=row['idempotency_key'],
            user_id=row['user_id'],
            source=row['source'],
            type=row['type'],
            delta_xp=row['delta_xp'],
            delta_balance=row['delta_balance'],
            reason=row['reason'],
            metadata=row.get('metadata'),
            created_at=row['created_at']
        )


@dataclass
class SyncState:
    """Модель состояния синхронизации пользователя"""
    user_id: int  # telegram_user_id
    
    # Последние значения Telegram
    last_telegram_xp: int
    last_telegram_balance: int
    last_telegram_rank: int
    
    # Последние значения Discord
    last_discord_xp: int
    last_discord_balance: int
    last_discord_rank: int
    
    # Reconcile
    last_reconcile_at: Optional[datetime]
    reconcile_errors: int
    
    # Метаданные
    updated_at: datetime
    
    @classmethod
    def from_db_row(cls, row):
        """Создать SyncState из строки БД"""
        if not row:
            return None
        
        return cls(
            user_id=row['user_id'],
            last_telegram_xp=row['last_telegram_xp'],
            last_telegram_balance=row['last_telegram_balance'],
            last_telegram_rank=row['last_telegram_rank'],
            last_discord_xp=row['last_discord_xp'],
            last_discord_balance=row['last_discord_balance'],
            last_discord_rank=row['last_discord_rank'],
            last_reconcile_at=row.get('last_reconcile_at'),
            reconcile_errors=row['reconcile_errors'],
            updated_at=row['updated_at']
        )
    
    @property
    def has_xp_diff(self) -> bool:
        """Есть ли расхождение в XP"""
        return abs(self.last_telegram_xp - self.last_discord_xp) > 10
    
    @property
    def has_balance_diff(self) -> bool:
        """Есть ли расхождение в балансе"""
        return abs(self.last_telegram_balance - self.last_discord_balance) > 10
    
    @property
    def has_rank_diff(self) -> bool:
        """Есть ли расхождение в ранге"""
        return self.last_telegram_rank != self.last_discord_rank


# ============================================================================
# УТИЛИТЫ
# ============================================================================

def generate_idempotency_key(
    source: str,
    event_type: str,
    entity_id: str,
    user_id: int,
    timestamp: Optional[int] = None
) -> str:
    """
    Генерировать ключ идемпотентности
    
    Args:
        source: telegram или discord
        event_type: тип события
        entity_id: ID сущности (game_id, achievement_id, etc)
        user_id: ID пользователя
        timestamp: Опциональная метка времени
    
    Returns:
        Уникальный ключ
    
    Examples:
        "tg_game_12345_67890"
        "ds_voice_session_abc_67890"
        "tg_achievement_first_win_67890"
    """
    if timestamp:
        return f"{source}_{event_type}_{entity_id}_{user_id}_{timestamp}"
    else:
        return f"{source}_{event_type}_{entity_id}_{user_id}"
