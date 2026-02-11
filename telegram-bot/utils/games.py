"""
Утилиты для игр
Версия 1.0 - логика игр, кулдауны, награды
"""

import random
from datetime import datetime, timedelta
from database import db

# ============================================================================
# УГАДАЙ ЧИСЛО (Guess Number)
# ============================================================================

def start_guess_number(telegram_id, bet_amount):
    """
    Начать игру "Угадай число"
    
    Args:
        telegram_id: ID пользователя
        bet_amount: Ставка (монеты)
    
    Returns:
        dict: {'success': bool, 'error': str, 'number': int}
    """
    user = db.get_user(telegram_id)
    
    # Проверка баланса
    if user['coins'] < bet_amount:
        return {
            'success': False,
            'error': f"Недостаточно монет! У тебя: {user['coins']}, нужно: {bet_amount}"
        }
    
    # Снимаем ставку
    if not db.remove_coins(telegram_id, bet_amount):
        return {
            'success': False,
            'error': "Ошибка снятия монет"
        }
    
    # Генерируем число от 1 до 10
    secret_number = random.randint(1, 10)
    
    return {
        'success': True,
        'number': secret_number,
        'bet': bet_amount
    }

def check_guess_number(telegram_id, secret_number, guessed_number, bet_amount):
    """
    Проверить угаданное число
    
    Returns:
        dict: {'won': bool, 'reward_coins': int, 'reward_xp': int}
    """
    won = (secret_number == guessed_number)
    
    if won:
        # Выигрыш: ставка * 3
        reward_coins = bet_amount * 3
        reward_xp = 50
        
        db.add_coins(telegram_id, reward_coins)
        db.add_xp(telegram_id, reward_xp)
        
        return {
            'won': True,
            'reward_coins': reward_coins,
            'reward_xp': reward_xp,
            'secret_number': secret_number
        }
    else:
        # Проигрыш: утешительный XP
        reward_xp = 5
        db.add_xp(telegram_id, reward_xp)
        
        return {
            'won': False,
            'reward_coins': 0,
            'reward_xp': reward_xp,
            'secret_number': secret_number
        }

# ============================================================================
# КВИЗ (Quiz)
# ============================================================================

QUIZ_QUESTIONS = [
    {
        'question': 'Сколько планет в Солнечной системе?',
        'options': ['7', '8', '9', '10'],
        'correct': 1  # индекс правильного ответа
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
    }
]

def get_random_quiz():
    """Получить случайный вопрос квиза"""
    return random.choice(QUIZ_QUESTIONS)

def check_quiz_answer(telegram_id, correct_index, user_answer_index, bet_amount):
    """
    Проверить ответ на квиз
    
    Returns:
        dict: {'correct': bool, 'reward_coins': int, 'reward_xp': int}
    """
    correct = (correct_index == user_answer_index)
    
    if correct:
        # Правильный ответ: ставка * 2
        reward_coins = bet_amount * 2
        reward_xp = 30
        
        db.add_coins(telegram_id, reward_coins)
        db.add_xp(telegram_id, reward_xp)
        
        return {
            'correct': True,
            'reward_coins': reward_coins,
            'reward_xp': reward_xp
        }
    else:
        # Неправильный ответ: теряем ставку, но получаем XP
        if not db.remove_coins(telegram_id, bet_amount):
            pass  # Уже сняли при старте
        
        reward_xp = 5
        db.add_xp(telegram_id, reward_xp)
        
        return {
            'correct': False,
            'reward_coins': -bet_amount,
            'reward_xp': reward_xp
        }

# ============================================================================
# ЕЖЕДНЕВНЫЙ СПИН (Daily Spin)
# ============================================================================

SPIN_REWARDS = [
    {'name': '💰 10 монет', 'coins': 10, 'xp': 5, 'weight': 30},
    {'name': '💰 25 монет', 'coins': 25, 'xp': 10, 'weight': 25},
    {'name': '💰 50 монет', 'coins': 50, 'xp': 15, 'weight': 20},
    {'name': '💰 100 монет', 'coins': 100, 'xp': 25, 'weight': 15},
    {'name': '💎 50 XP', 'coins': 0, 'xp': 50, 'weight': 5},
    {'name': '🎁 200 монет', 'coins': 200, 'xp': 50, 'weight': 3},
    {'name': '🎉 ДЖЕКПОТ!', 'coins': 500, 'xp': 100, 'weight': 2},
]

def can_spin(telegram_id):
    """
    Проверить можно ли крутить спин
    
    Returns:
        dict: {'can_spin': bool, 'time_left': str}
    """
    user = db.get_user(telegram_id)
    last_spin = user.get('last_spin')
    
    if not last_spin:
        return {'can_spin': True, 'time_left': None}
    
    last_spin_time = datetime.fromisoformat(last_spin)
    now = datetime.now()
    time_diff = (now - last_spin_time).total_seconds()
    
    # 24 часа = 86400 секунд
    if time_diff >= 86400:
        return {'can_spin': True, 'time_left': None}
    
    time_left = 86400 - time_diff
    hours = int(time_left // 3600)
    minutes = int((time_left % 3600) // 60)
    
    return {
        'can_spin': False,
        'time_left': f"{hours}ч {minutes}м"
    }

def spin_wheel(telegram_id):
    """
    Крутить колесо фортуны
    
    Returns:
        dict: {'success': bool, 'error': str, 'reward': dict}
    """
    # Проверка кулдауна
    check = can_spin(telegram_id)
    if not check['can_spin']:
        return {
            'success': False,
            'error': f"Ты уже крутил сегодня! Следующий спин через {check['time_left']}"
        }
    
    # Выбираем награду с учётом весов
    rewards = []
    weights = []
    for reward in SPIN_REWARDS:
        rewards.append(reward)
        weights.append(reward['weight'])
    
    selected_reward = random.choices(rewards, weights=weights, k=1)[0]
    
    # Выдаём награду
    if selected_reward['coins'] > 0:
        db.add_coins(telegram_id, selected_reward['coins'])
    
    if selected_reward['xp'] > 0:
        db.add_xp(telegram_id, selected_reward['xp'])
    
    # Обновляем время последнего спина
    user = db.get_user(telegram_id)
    user['last_spin'] = datetime.now().isoformat()
    db.update_user(telegram_id, last_spin=user['last_spin'])
    
    return {
        'success': True,
        'reward': selected_reward
    }

# ============================================================================
# СТАТИСТИКА ИГР
# ============================================================================

def get_game_stats(telegram_id):
    """Получить статистику игр пользователя"""
    user = db.get_user(telegram_id)
    
    return {
        'games_played': user.get('games_played', 0),
        'games_won': user.get('games_won', 0),
        'total_coins_won': user.get('total_coins_won', 0),
        'last_spin': user.get('last_spin')
    }

def update_game_stats(telegram_id, won=False, coins_won=0):
    """Обновить статистику игр"""
    user = db.get_user(telegram_id)
    
    user['games_played'] = user.get('games_played', 0) + 1
    
    if won:
        user['games_won'] = user.get('games_won', 0) + 1
    
    user['total_coins_won'] = user.get('total_coins_won', 0) + coins_won
    
    # Обновляем только нужные поля
    db.update_user(
        telegram_id,
        games_played=user['games_played'],
        games_won=user.get('games_won', 0),
        total_coins_won=user['total_coins_won']
    )

