"""
User domain model
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Модель пользователя"""
    id: int
    telegram_id: str
    username: str
    first_name: str
    xp: int
    coins: int
    rank_id: int
    role: str
    created_at: datetime
    last_active: datetime
    last_daily: Optional[datetime] = None
    last_spin: Optional[datetime] = None
    discord_id: Optional[str] = None
    is_banned: bool = False
    ban_reason: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row):
        """Создать User из строки БД"""
        if not row:
            return None
        
        return cls(
            id=row['id'],
            telegram_id=row['telegram_id'],
            username=row['username'] or '',
            first_name=row['first_name'] or '',
            xp=row['xp'],
            coins=row['coins'],
            rank_id=row['rank_id'],
            role=row['role'],
            created_at=row['created_at'],
            last_active=row['last_active'],
            last_daily=row.get('last_daily'),
            last_spin=row.get('last_spin'),
            discord_id=row.get('discord_id'),
            is_banned=row.get('is_banned', False),
            ban_reason=row.get('ban_reason')
        )
    
    def to_dict(self) -> dict:
        """Конвертировать в словарь"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'xp': self.xp,
            'coins': self.coins,
            'rank_id': self.rank_id,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'last_daily': self.last_daily.isoformat() if self.last_daily else None,
            'last_spin': self.last_spin.isoformat() if self.last_spin else None,
            'discord_id': self.discord_id,
            'is_banned': self.is_banned,
            'ban_reason': self.ban_reason
        }


@dataclass
class Rank:
    """Модель ранга"""
    id: int
    name: str
    color: str
    required_xp: int
    reward_coins: int
    
    @classmethod
    def from_dict(cls, data: dict):
        """Создать Rank из словаря"""
        return cls(
            id=data['id'],
            name=data['name'],
            color=data['color'],
            required_xp=data['required_xp'],
            reward_coins=data['reward_coins']
        )


# 20 рангов TTFD
RANKS = [
    Rank(1, "Пустой взгляд", "#95a5a6", 0, 0),
    Rank(2, "Потерянный", "#7f8c8d", 500, 50),
    Rank(3, "Холодный", "#5d6d7e", 1250, 100),
    Rank(4, "Без сна", "#34495e", 2250, 150),
    Rank(5, "Ночной", "#2c3e50", 3500, 200),
    Rank(6, "Тихий", "#566573", 5000, 300),
    Rank(7, "Гулёныш", "#616a6b", 6750, 400),
    Rank(8, "Отрешённый", "#515a5a", 8750, 500),
    Rank(9, "Бледный", "#424949", 11000, 700),
    Rank(10, "Полумёртвый", "#2e4053", 13500, 900),
    Rank(11, "Гуль", "#1c2833", 16250, 1200),
    Rank(12, "Безэмо", "#17202a", 19250, 1500),
    Rank(13, "Пожиратель тишины", "#641e16", 22500, 2000),
    Rank(14, "Сломанный", "#512e5f", 26000, 2500),
    Rank(15, "Чёрное сердце", "#1a1a1a", 29750, 3000),
    Rank(16, "Носитель тьмы", "#0d0d0d", 33750, 4000),
    Rank(17, "Первый кошмар", "#4a235a", 38000, 5000),
    Rank(18, "Глава ночи", "#1b2631", 42500, 7000),
    Rank(19, "Король пустоты", "#000000", 47250, 10000),
    Rank(20, "Абсолютный гуль", "#8b0000", 52250, 15000),
]


def get_rank_by_id(rank_id: int) -> Rank:
    """Получить ранг по ID"""
    if 1 <= rank_id <= len(RANKS):
        return RANKS[rank_id - 1]
    return RANKS[0]


def calculate_rank_by_xp(xp: int) -> Rank:
    """Вычислить ранг по XP"""
    current_rank = RANKS[0]
    for rank in RANKS:
        if xp >= rank.required_xp:
            current_rank = rank
    return current_rank
