"""
Discord Link models - модели привязки Telegram ↔ Discord
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class LinkStatus(Enum):
    """Статус привязки"""
    PENDING = "pending"  # Ожидает подтверждения
    ACTIVE = "active"  # Активна
    EXPIRED = "expired"  # Код истёк
    REVOKED = "revoked"  # Отозвана


@dataclass
class DiscordLink:
    """Модель привязки Telegram ↔ Discord"""
    id: int
    telegram_user_id: int
    discord_user_id: Optional[int]  # None пока не подтверждено
    
    # Код подтверждения
    verification_code: str  # 6-значный код
    
    # Статус
    status: str  # pending, active, expired, revoked
    
    # Метаданные
    created_at: datetime
    verified_at: Optional[datetime]
    expires_at: datetime  # Код действителен 15 минут
    
    @property
    def is_active(self) -> bool:
        """Активна ли привязка"""
        return self.status == LinkStatus.ACTIVE.value
    
    @property
    def is_pending(self) -> bool:
        """Ожидает ли подтверждения"""
        return self.status == LinkStatus.PENDING.value
    
    @property
    def is_expired(self) -> bool:
        """Истёк ли код"""
        if self.status == LinkStatus.EXPIRED.value:
            return True
        
        if self.is_pending and datetime.now() > self.expires_at:
            return True
        
        return False


@dataclass
class DiscordRoleGrant:
    """Модель выдачи Discord роли"""
    id: int
    telegram_user_id: int
    discord_user_id: int
    
    # Роль
    role_name: str  # Название роли (например: "achievement_pro")
    role_id: Optional[str]  # ID роли в Discord (если известен)
    
    # Причина выдачи
    reason_type: str  # achievement, season_reward, rank, manual
    reason_id: Optional[str]  # ID достижения/сезона/etc
    
    # Статус
    is_granted: bool  # Выдана ли роль
    granted_at: Optional[datetime]
    
    # Ошибки
    error_message: Optional[str]
    retry_count: int
    
    # Метаданные
    created_at: datetime
    updated_at: datetime


@dataclass
class DiscordSyncLog:
    """Лог синхронизации с Discord"""
    id: int
    telegram_user_id: int
    discord_user_id: int
    
    # Действие
    action: str  # link_created, role_granted, role_revoked, sync_failed
    
    # Детали
    details: dict  # JSON с деталями
    
    # Результат
    success: bool
    error_message: Optional[str]
    
    # Метаданные
    created_at: datetime
