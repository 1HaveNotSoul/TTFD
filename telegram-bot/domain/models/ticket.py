"""
Ticket models - модели тикетов
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TicketStatus(Enum):
    """Статус тикета"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class TicketPriority(Enum):
    """Приоритет тикета"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TicketCategory(Enum):
    """Категория тикета"""
    GENERAL = "general"
    TECHNICAL = "technical"
    SUGGESTION = "suggestion"
    COMPLAINT = "complaint"


@dataclass
class Ticket:
    """Тикет поддержки"""
    id: Optional[int] = None
    user_id: int = 0
    category: str = TicketCategory.GENERAL.value
    priority: str = TicketPriority.MEDIUM.value
    status: str = TicketStatus.OPEN.value
    subject: str = ""
    assigned_to: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    sla_deadline: Optional[datetime] = None
    
    # Дополнительные поля (не из БД)
    messages: List['TicketMessage'] = None
    user_name: str = ""
    assigned_to_name: Optional[str] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
    
    @staticmethod
    def from_db_row(row) -> Optional['Ticket']:
        """Создать из строки БД"""
        if not row:
            return None
        
        return Ticket(
            id=row['id'],
            user_id=row['user_id'],
            category=row['category'],
            priority=row['priority'],
            status=row['status'],
            subject=row['subject'],
            assigned_to=row.get('assigned_to'),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            closed_at=row.get('closed_at'),
            sla_deadline=row.get('sla_deadline')
        )


@dataclass
class TicketMessage:
    """Сообщение в тикете"""
    id: Optional[int] = None
    ticket_id: int = 0
    user_id: int = 0
    message: str = ""
    is_admin: bool = False
    created_at: Optional[datetime] = None
    
    # Дополнительные поля
    user_name: str = ""
    
    @staticmethod
    def from_db_row(row) -> Optional['TicketMessage']:
        """Создать из строки БД"""
        if not row:
            return None
        
        return TicketMessage(
            id=row['id'],
            ticket_id=row['ticket_id'],
            user_id=row['user_id'],
            message=row['message'],
            is_admin=row['is_admin'],
            created_at=row['created_at']
        )


@dataclass
class TicketStats:
    """Статистика тикетов"""
    total: int = 0
    open: int = 0
    in_progress: int = 0
    closed: int = 0
    high_priority: int = 0
    medium_priority: int = 0
    low_priority: int = 0
    avg_response_time: float = 0.0  # в часах
    avg_resolution_time: float = 0.0  # в часах


# Названия категорий
CATEGORY_NAMES = {
    TicketCategory.GENERAL.value: '📋 Общий вопрос',
    TicketCategory.TECHNICAL.value: '🔧 Техническая проблема',
    TicketCategory.SUGGESTION.value: '💡 Предложение',
    TicketCategory.COMPLAINT.value: '⚠️ Жалоба'
}

# Названия приоритетов
PRIORITY_NAMES = {
    TicketPriority.LOW.value: '🟢 Низкий',
    TicketPriority.MEDIUM.value: '🟡 Средний',
    TicketPriority.HIGH.value: '🔴 Высокий'
}

# Эмодзи статусов
STATUS_EMOJI = {
    TicketStatus.OPEN.value: '🆕',
    TicketStatus.IN_PROGRESS.value: '🔄',
    TicketStatus.CLOSED.value: '✅'
}
