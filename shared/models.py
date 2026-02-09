"""
Shared Models - Общие модели для всех платформ
Используется Telegram Bot, Discord Bot и Website
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class Platform(Enum):
    """Платформа пользователя"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WEBSITE = "website"


@dataclass
class UnifiedUser:
    """
    Унифицированная модель пользователя для всех платформ
    """
    # Основные ID
    id: int  # Внутренний ID в БД
    telegram_id: Optional[str] = None
    discord_id: Optional[str] = None
    website_email: Optional[str] = None
    
    # Основная информация
    username: str = "Unknown"
    display_name: str = "Unknown"
    
    # Игровые данные
    xp: int = 0
    coins: int = 0
    rank_id: int = 1
    
    # Статистика
    games_played: int = 0
    games_won: int = 0
    total_voice_time: int = 0  # Секунды в войсе Discord
    messages_sent: int = 0
    
    # Достижения и прогресс
    achievements: List[str] = None
    current_season_xp: int = 0
    season_rank: int = 0
    daily_streak: int = 0
    
    # Метаданные
    created_at: datetime = None
    last_active: datetime = None
    last_daily: Optional[datetime] = None
    
    # Привязки платформ
    platforms: List[str] = None  # ['telegram', 'discord', 'website']
    primary_platform: str = "telegram"
    
    def __post_init__(self):
        if self.achievements is None:
            self.achievements = []
        if self.platforms is None:
            self.platforms = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_active is None:
            self.last_active = datetime.now()
    
    @property
    def is_linked_telegram(self) -> bool:
        """Привязан ли Telegram"""
        return self.telegram_id is not None
    
    @property
    def is_linked_discord(self) -> bool:
        """Привязан ли Discord"""
        return self.discord_id is not None
    
    @property
    def is_linked_website(self) -> bool:
        """Привязан ли Website"""
        return self.website_email is not None
    
    @property
    def linked_platforms_count(self) -> int:
        """Количество привязанных платформ"""
        return len(self.platforms)
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'discord_id': self.discord_id,
            'website_email': self.website_email,
            'username': self.username,
            'display_name': self.display_name,
            'xp': self.xp,
            'coins': self.coins,
            'rank_id': self.rank_id,
            'games_played': self.games_played,
            'games_won': self.games_won,
            'total_voice_time': self.total_voice_time,
            'messages_sent': self.messages_sent,
            'achievements': self.achievements,
            'current_season_xp': self.current_season_xp,
            'season_rank': self.season_rank,
            'daily_streak': self.daily_streak,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'last_daily': self.last_daily.isoformat() if self.last_daily else None,
            'platforms': self.platforms,
            'primary_platform': self.primary_platform
        }


@dataclass
class Rank:
    """Модель ранга (одинаковая для всех платформ)"""
    id: int
    name: str
    tier: str  # F, E, D, C, B, A, S
    stars: int  # 1, 2, 3
    color: str
    required_xp: int
    reward_coins: int
    emoji: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'tier': self.tier,
            'stars': self.stars,
            'color': self.color,
            'required_xp': self.required_xp,
            'reward_coins': self.reward_coins,
            'emoji': self.emoji
        }


# 20 рангов TTFD (единые для всех платформ)
UNIFIED_RANKS = [
    # Ранг F (1-3)
    Rank(1, "Ранг F I", "F", 1, "#95a5a6", 0, 0, "<:F:1467727827473530931>"),
    Rank(2, "Ранг F II", "F", 2, "#7f8c8d", 500, 50, "<:F:1467727827473530931>"),
    Rank(3, "Ранг F III", "F", 3, "#5d6d7e", 1250, 100, "<:F:1467727827473530931>"),
    
    # Ранг E (4-6)
    Rank(4, "Ранг E I", "E", 1, "#34495e", 2250, 150, "<:E:1467727807001137336>"),
    Rank(5, "Ранг E II", "E", 2, "#2c3e50", 3500, 200, "<:E:1467727807001137336>"),
    Rank(6, "Ранг E III", "E", 3, "#566573", 5000, 300, "<:E:1467727807001137336>"),
    
    # Ранг D (7-9)
    Rank(7, "Ранг D I", "D", 1, "#616a6b", 6750, 400, "<:D:1467727832456233113>"),
    Rank(8, "Ранг D II", "D", 2, "#515a5a", 8750, 500, "<:D:1467727832456233113>"),
    Rank(9, "Ранг D III", "D", 3, "#424949", 11000, 700, "<:D:1467727832456233113>"),
    
    # Ранг C (10-12)
    Rank(10, "Ранг C I", "C", 1, "#2e4053", 13500, 900, "<:C:1467727811480649940>"),
    Rank(11, "Ранг C II", "C", 2, "#1c2833", 16250, 1200, "<:C:1467727811480649940>"),
    Rank(12, "Ранг C III", "C", 3, "#17202a", 19250, 1500, "<:C:1467727811480649940>"),
    
    # Ранг B (13-15)
    Rank(13, "Ранг B I", "B", 1, "#641e16", 22500, 2000, "<:B:1467727824558231653>"),
    Rank(14, "Ранг B II", "B", 2, "#512e5f", 26000, 2500, "<:B:1467727824558231653>"),
    Rank(15, "Ранг B III", "B", 3, "#1a1a1a", 29750, 3000, "<:B:1467727824558231653>"),
    
    # Ранг A (16-18)
    Rank(16, "Ранг A I", "A", 1, "#0d0d0d", 33750, 4000, "<:A:1467727451500187718>"),
    Rank(17, "Ранг A II", "A", 2, "#4a235a", 38000, 5000, "<:A:1467727451500187718>"),
    Rank(18, "Ранг A III", "A", 3, "#1b2631", 42500, 7000, "<:A:1467727451500187718>"),
    
    # Ранг S (19-20)
    Rank(19, "Ранг S I", "S", 1, "#8b0000", 47250, 10000, "<:S:1467727794296328234>"),
    Rank(20, "Ранг S II", "S", 2, "#ff0000", 52250, 15000, "<:S:1467727794296328234>"),
]


def get_rank_by_id(rank_id: int) -> Rank:
    """Получить ранг по ID"""
    if 1 <= rank_id <= len(UNIFIED_RANKS):
        return UNIFIED_RANKS[rank_id - 1]
    return UNIFIED_RANKS[0]


def calculate_rank_by_xp(xp: int) -> Rank:
    """Вычислить ранг по XP"""
    current_rank = UNIFIED_RANKS[0]
    for rank in UNIFIED_RANKS:
        if xp >= rank.required_xp:
            current_rank = rank
    return current_rank


def get_rank_tier_for_xp(xp: int) -> str:
    """Получить tier ранга по XP (F, E, D, C, B, A, S)"""
    rank = calculate_rank_by_xp(xp)
    return rank.tier


@dataclass
class PlatformLink:
    """Модель привязки платформ"""
    id: int
    user_id: int  # ID в unified_users
    
    # Платформы
    telegram_id: Optional[str] = None
    discord_id: Optional[str] = None
    website_email: Optional[str] = None
    
    # Статус
    is_active: bool = True
    
    # Метаданные
    linked_at: datetime = None
    last_sync_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.linked_at is None:
            self.linked_at = datetime.now()


@dataclass
class CrossPlatformEvent:
    """Событие для синхронизации между платформами"""
    id: str  # UUID
    user_id: int
    
    # Тип события
    event_type: str  # xp_change, coins_change, rank_up, achievement_unlock
    
    # Источник
    source_platform: str  # telegram, discord, website
    
    # Данные
    data: Dict[str, Any]
    
    # Статус
    processed: bool = False
    processed_at: Optional[datetime] = None
    
    # Метаданные
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
