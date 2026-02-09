"""
Season models - модели сезонов
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class SeasonStatus(Enum):
    """Статус сезона"""
    ACTIVE = "active"
    ENDED = "ended"
    UPCOMING = "upcoming"


@dataclass
class Season:
    """Модель сезона"""
    id: int
    number: int  # Номер сезона (1, 2, 3...)
    name: str  # Название сезона
    start_date: datetime
    end_date: datetime
    status: str  # active, ended, upcoming
    
    # Награды за топ позиции
    rewards_config: dict  # JSON с наградами
    
    # Метаданные
    created_at: datetime
    
    @property
    def is_active(self) -> bool:
        """Активен ли сезон"""
        return self.status == SeasonStatus.ACTIVE.value
    
    @property
    def days_left(self) -> int:
        """Сколько дней осталось"""
        if not self.is_active:
            return 0
        delta = self.end_date - datetime.now()
        return max(0, delta.days)
    
    @property
    def duration_days(self) -> int:
        """Длительность сезона в днях"""
        delta = self.end_date - self.start_date
        return delta.days


@dataclass
class SeasonProgress:
    """Прогресс пользователя в сезоне"""
    id: int
    user_id: int
    season_id: int
    
    # Сезонная статистика
    season_xp: int  # XP заработанный в этом сезоне
    season_coins: int  # Монеты заработанные в этом сезоне
    games_played: int  # Игр сыграно
    games_won: int  # Игр выиграно
    
    # Стрики
    current_streak: int  # Текущий стрик (дни подряд)
    best_streak: int  # Лучший стрик в сезоне
    last_activity_date: Optional[datetime]  # Последняя активность
    
    # Рейтинг
    rank: Optional[int]  # Позиция в рейтинге (обновляется периодически)
    
    # Награды
    rewards_claimed: bool  # Получены ли награды за сезон
    
    # Метаданные
    created_at: datetime
    updated_at: datetime
    
    @property
    def win_rate(self) -> float:
        """Процент побед"""
        if self.games_played == 0:
            return 0.0
        return (self.games_won / self.games_played) * 100


@dataclass
class SeasonReward:
    """Награда за сезон"""
    rank_from: int  # От какой позиции
    rank_to: int  # До какой позиции
    xp: int  # Награда XP
    coins: int  # Награда монет
    discord_role: Optional[str]  # Discord роль (если есть)
    title: Optional[str]  # Титул (если есть)


# Конфигурация наград по умолчанию
DEFAULT_SEASON_REWARDS = [
    {
        "rank_from": 1,
        "rank_to": 1,
        "xp": 5000,
        "coins": 1000,
        "discord_role": "season_champion",
        "title": "🏆 Чемпион сезона"
    },
    {
        "rank_from": 2,
        "rank_to": 3,
        "xp": 3000,
        "coins": 500,
        "discord_role": "season_top3",
        "title": "🥈 Топ-3 сезона"
    },
    {
        "rank_from": 4,
        "rank_to": 10,
        "xp": 2000,
        "coins": 300,
        "discord_role": "season_top10",
        "title": "🥉 Топ-10 сезона"
    },
    {
        "rank_from": 11,
        "rank_to": 50,
        "xp": 1000,
        "coins": 150,
        "discord_role": None,
        "title": "⭐ Топ-50 сезона"
    }
]
