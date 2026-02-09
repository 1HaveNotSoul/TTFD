"""
Game models - модели игр
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class GameType(Enum):
    """Типы игр"""
    GUESS_NUMBER = "guess_number"
    QUIZ = "quiz"
    SPIN = "spin"


class GameStatus(Enum):
    """Статус игры"""
    IN_PROGRESS = "in_progress"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


@dataclass
class GameSession:
    """Игровая сессия"""
    id: Optional[int] = None
    user_id: int = 0
    game_type: str = GameType.GUESS_NUMBER.value
    bet_amount: int = 0
    status: str = GameStatus.IN_PROGRESS.value
    result: Optional[dict] = None  # JSON с результатом игры
    reward_coins: int = 0
    reward_xp: int = 0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @staticmethod
    def from_db_row(row) -> Optional['GameSession']:
        """Создать из строки БД"""
        if not row:
            return None
        
        return GameSession(
            id=row['id'],
            user_id=row['user_id'],
            game_type=row['game_type'],
            bet_amount=row['bet_amount'],
            status=row['status'],
            result=row['result'],
            reward_coins=row['reward_coins'],
            reward_xp=row['reward_xp'],
            created_at=row['created_at'],
            completed_at=row['completed_at']
        )


@dataclass
class GameStats:
    """Статистика игр пользователя"""
    user_id: int
    total_games: int = 0
    total_wins: int = 0
    total_losses: int = 0
    total_coins_won: int = 0
    total_coins_lost: int = 0
    total_xp_earned: int = 0
    
    # По типам игр
    guess_games: int = 0
    guess_wins: int = 0
    quiz_games: int = 0
    quiz_wins: int = 0
    spin_count: int = 0
    
    last_spin_at: Optional[datetime] = None
    
    @property
    def win_rate(self) -> float:
        """Процент побед"""
        if self.total_games == 0:
            return 0.0
        return (self.total_wins / self.total_games) * 100
    
    @property
    def net_profit(self) -> int:
        """Чистая прибыль"""
        return self.total_coins_won - self.total_coins_lost


# Вопросы для квиза
QUIZ_QUESTIONS = [
    {
        'question': 'Сколько планет в Солнечной системе?',
        'options': ['7', '8', '9', '10'],
        'correct': 1
    },
    {
        'question': 'Какой язык программирования используется для создания этого бота?',
        'options': ['JavaScript', 'Python', 'Java', 'C++'],
        'correct': 1
    },
    {
        'question': 'Сколько континентов на Земле?',
        'options': ['5', '6', '7', '8'],
        'correct': 2
    },
    {
        'question': 'Какая самая большая планета в Солнечной системе?',
        'options': ['Земля', 'Марс', 'Юпитер', 'Сатурн'],
        'correct': 2
    },
    {
        'question': 'Сколько дней в високосном году?',
        'options': ['364', '365', '366', '367'],
        'correct': 2
    },
    {
        'question': 'Какой элемент имеет химический символ "O"?',
        'options': ['Золото', 'Кислород', 'Осмий', 'Олово'],
        'correct': 1
    },
    {
        'question': 'Сколько букв в русском алфавите?',
        'options': ['30', '31', '32', '33'],
        'correct': 3
    },
    {
        'question': 'Какая столица России?',
        'options': ['Санкт-Петербург', 'Москва', 'Казань', 'Новосибирск'],
        'correct': 1
    },
    {
        'question': 'Сколько часов в сутках?',
        'options': ['12', '24', '36', '48'],
        'correct': 1
    },
    {
        'question': 'Какой океан самый большой?',
        'options': ['Атлантический', 'Индийский', 'Тихий', 'Северный Ледовитый'],
        'correct': 2
    }
]

# Награды для спина
SPIN_REWARDS = [
    {'name': '💰 10 монет', 'coins': 10, 'xp': 5, 'weight': 30},
    {'name': '💰 25 монет', 'coins': 25, 'xp': 10, 'weight': 25},
    {'name': '💰 50 монет', 'coins': 50, 'xp': 15, 'weight': 20},
    {'name': '💰 100 монет', 'coins': 100, 'xp': 25, 'weight': 15},
    {'name': '💎 50 XP', 'coins': 0, 'xp': 50, 'weight': 5},
    {'name': '🎁 200 монет', 'coins': 200, 'xp': 50, 'weight': 3},
    {'name': '🎉 ДЖЕКПОТ!', 'coins': 500, 'xp': 100, 'weight': 2},
]
