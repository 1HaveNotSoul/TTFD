"""
Achievement models - модели достижений
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class AchievementCategory(Enum):
    """Категории достижений"""
    GAMES = "games"  # За игры
    ACTIVITY = "activity"  # За активность
    STREAK = "streak"  # За стрики
    TICKETS = "tickets"  # За тикеты
    SEASON = "season"  # За сезоны
    SPECIAL = "special"  # Специальные


class AchievementRarity(Enum):
    """Редкость достижений"""
    COMMON = "common"  # Обычное
    RARE = "rare"  # Редкое
    EPIC = "epic"  # Эпическое
    LEGENDARY = "legendary"  # Легендарное


@dataclass
class Achievement:
    """Модель достижения"""
    id: str  # Уникальный ID (например: "first_win")
    name: str  # Название
    description: str  # Описание
    category: str  # Категория
    rarity: str  # Редкость
    
    # Условия получения
    requirement_type: str  # Тип требования (games_won, streak_days, etc.)
    requirement_value: int  # Значение требования
    
    # Награды
    reward_xp: int
    reward_coins: int
    reward_discord_role: Optional[str]  # Discord роль (если есть)
    
    # Иконка
    icon: str  # Эмодзи
    
    # Метаданные
    is_hidden: bool  # Скрытое достижение
    created_at: datetime


@dataclass
class UserAchievement:
    """Прогресс пользователя по достижению"""
    id: int
    user_id: int
    achievement_id: str
    
    # Прогресс
    current_progress: int  # Текущий прогресс
    required_progress: int  # Требуемый прогресс
    
    # Статус
    is_completed: bool
    completed_at: Optional[datetime]
    
    # Награды
    rewards_claimed: bool
    
    # Метаданные
    created_at: datetime
    updated_at: datetime
    
    @property
    def progress_percent(self) -> float:
        """Процент выполнения"""
        if self.required_progress == 0:
            return 100.0
        return min(100.0, (self.current_progress / self.required_progress) * 100)


# ============================================================================
# КОНФИГУРАЦИЯ ДОСТИЖЕНИЙ
# ============================================================================

DEFAULT_ACHIEVEMENTS = [
    # ========================================================================
    # ИГРЫ
    # ========================================================================
    {
        "id": "first_win",
        "name": "Первая победа",
        "description": "Выиграй свою первую игру",
        "category": "games",
        "rarity": "common",
        "requirement_type": "games_won",
        "requirement_value": 1,
        "reward_xp": 100,
        "reward_coins": 50,
        "reward_discord_role": None,
        "icon": "🎯",
        "is_hidden": False
    },
    {
        "id": "winner_10",
        "name": "Везунчик",
        "description": "Выиграй 10 игр",
        "category": "games",
        "rarity": "common",
        "requirement_type": "games_won",
        "requirement_value": 10,
        "reward_xp": 200,
        "reward_coins": 100,
        "reward_discord_role": None,
        "icon": "🎲",
        "is_hidden": False
    },
    {
        "id": "winner_50",
        "name": "Профессионал",
        "description": "Выиграй 50 игр",
        "category": "games",
        "rarity": "rare",
        "requirement_type": "games_won",
        "requirement_value": 50,
        "reward_xp": 500,
        "reward_coins": 300,
        "reward_discord_role": "achievement_pro",
        "icon": "🏅",
        "is_hidden": False
    },
    {
        "id": "winner_100",
        "name": "Мастер игр",
        "description": "Выиграй 100 игр",
        "category": "games",
        "rarity": "epic",
        "requirement_type": "games_won",
        "requirement_value": 100,
        "reward_xp": 1000,
        "reward_coins": 500,
        "reward_discord_role": "achievement_master",
        "icon": "🏆",
        "is_hidden": False
    },
    {
        "id": "winner_500",
        "name": "Легенда",
        "description": "Выиграй 500 игр",
        "category": "games",
        "rarity": "legendary",
        "requirement_type": "games_won",
        "requirement_value": 500,
        "reward_xp": 5000,
        "reward_coins": 2000,
        "reward_discord_role": "achievement_legend",
        "icon": "👑",
        "is_hidden": False
    },
    
    # ========================================================================
    # АКТИВНОСТЬ
    # ========================================================================
    {
        "id": "active_player",
        "name": "Активный игрок",
        "description": "Сыграй 100 игр",
        "category": "activity",
        "rarity": "common",
        "requirement_type": "games_played",
        "requirement_value": 100,
        "reward_xp": 300,
        "reward_coins": 150,
        "reward_discord_role": None,
        "icon": "⚡",
        "is_hidden": False
    },
    {
        "id": "dedicated_player",
        "name": "Преданный игрок",
        "description": "Сыграй 500 игр",
        "category": "activity",
        "rarity": "rare",
        "requirement_type": "games_played",
        "requirement_value": 500,
        "reward_xp": 1000,
        "reward_coins": 500,
        "reward_discord_role": "achievement_dedicated",
        "icon": "💪",
        "is_hidden": False
    },
    {
        "id": "rich_player",
        "name": "Богач",
        "description": "Накопи 10000 монет",
        "category": "activity",
        "rarity": "rare",
        "requirement_type": "total_coins",
        "requirement_value": 10000,
        "reward_xp": 500,
        "reward_coins": 1000,
        "reward_discord_role": None,
        "icon": "💰",
        "is_hidden": False
    },
    {
        "id": "experienced",
        "name": "Опытный",
        "description": "Достигни 10000 XP",
        "category": "activity",
        "rarity": "rare",
        "requirement_type": "total_xp",
        "requirement_value": 10000,
        "reward_xp": 1000,
        "reward_coins": 500,
        "reward_discord_role": None,
        "icon": "⭐",
        "is_hidden": False
    },
    
    # ========================================================================
    # СТРИКИ
    # ========================================================================
    {
        "id": "streak_3",
        "name": "Постоянство",
        "description": "Играй 3 дня подряд",
        "category": "streak",
        "rarity": "common",
        "requirement_type": "streak_days",
        "requirement_value": 3,
        "reward_xp": 150,
        "reward_coins": 75,
        "reward_discord_role": None,
        "icon": "🔥",
        "is_hidden": False
    },
    {
        "id": "streak_7",
        "name": "Неделя силы",
        "description": "Играй 7 дней подряд",
        "category": "streak",
        "rarity": "rare",
        "requirement_type": "streak_days",
        "requirement_value": 7,
        "reward_xp": 500,
        "reward_coins": 250,
        "reward_discord_role": "achievement_streak7",
        "icon": "🔥🔥",
        "is_hidden": False
    },
    {
        "id": "streak_30",
        "name": "Месяц преданности",
        "description": "Играй 30 дней подряд",
        "category": "streak",
        "rarity": "epic",
        "requirement_type": "streak_days",
        "requirement_value": 30,
        "reward_xp": 2000,
        "reward_coins": 1000,
        "reward_discord_role": "achievement_streak30",
        "icon": "🔥🔥🔥",
        "is_hidden": False
    },
    
    # ========================================================================
    # ТИКЕТЫ
    # ========================================================================
    {
        "id": "first_ticket",
        "name": "Первое обращение",
        "description": "Создай свой первый тикет",
        "category": "tickets",
        "rarity": "common",
        "requirement_type": "tickets_created",
        "requirement_value": 1,
        "reward_xp": 50,
        "reward_coins": 25,
        "reward_discord_role": None,
        "icon": "🎫",
        "is_hidden": False
    },
    {
        "id": "helpful_user",
        "name": "Полезный пользователь",
        "description": "Получи 5 решённых тикетов",
        "category": "tickets",
        "rarity": "rare",
        "requirement_type": "tickets_resolved",
        "requirement_value": 5,
        "reward_xp": 300,
        "reward_coins": 150,
        "reward_discord_role": None,
        "icon": "✅",
        "is_hidden": False
    },
    
    # ========================================================================
    # СЕЗОНЫ
    # ========================================================================
    {
        "id": "season_participant",
        "name": "Участник сезона",
        "description": "Сыграй хотя бы одну игру в сезоне",
        "category": "season",
        "rarity": "common",
        "requirement_type": "season_games",
        "requirement_value": 1,
        "reward_xp": 100,
        "reward_coins": 50,
        "reward_discord_role": None,
        "icon": "🎮",
        "is_hidden": False
    },
    {
        "id": "season_top50",
        "name": "Топ-50 сезона",
        "description": "Попади в топ-50 сезона",
        "category": "season",
        "rarity": "rare",
        "requirement_type": "season_rank",
        "requirement_value": 50,
        "reward_xp": 500,
        "reward_coins": 250,
        "reward_discord_role": None,
        "icon": "🌟",
        "is_hidden": False
    },
    {
        "id": "season_top10",
        "name": "Топ-10 сезона",
        "description": "Попади в топ-10 сезона",
        "category": "season",
        "rarity": "epic",
        "requirement_type": "season_rank",
        "requirement_value": 10,
        "reward_xp": 1500,
        "reward_coins": 750,
        "reward_discord_role": "achievement_season_top10",
        "icon": "💎",
        "is_hidden": False
    },
    {
        "id": "season_champion",
        "name": "Чемпион сезона",
        "description": "Стань первым в сезоне",
        "category": "season",
        "rarity": "legendary",
        "requirement_type": "season_rank",
        "requirement_value": 1,
        "reward_xp": 5000,
        "reward_coins": 2500,
        "reward_discord_role": "achievement_season_champion",
        "icon": "👑",
        "is_hidden": False
    },
    
    # ========================================================================
    # СПЕЦИАЛЬНЫЕ
    # ========================================================================
    {
        "id": "lucky_spin",
        "name": "Удача улыбнулась",
        "description": "Выиграй джекпот в спине",
        "category": "special",
        "rarity": "epic",
        "requirement_type": "spin_jackpot",
        "requirement_value": 1,
        "reward_xp": 1000,
        "reward_coins": 500,
        "reward_discord_role": None,
        "icon": "🎰",
        "is_hidden": True
    },
    {
        "id": "perfect_quiz",
        "name": "Эрудит",
        "description": "Ответь правильно на 10 квизов подряд",
        "category": "special",
        "rarity": "epic",
        "requirement_type": "quiz_streak",
        "requirement_value": 10,
        "reward_xp": 1500,
        "reward_coins": 750,
        "reward_discord_role": "achievement_erudite",
        "icon": "🧠",
        "is_hidden": True
    }
]
