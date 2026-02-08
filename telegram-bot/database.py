"""
База данных для Telegram бота
Хранит пользователей, их прогресс, ранги и статистику
"""

import json
import os
from datetime import datetime
from config import DATABASE_FILE

# 20 рангов TTFD
RANKS = [
    {"id": 1, "name": "Пустой взгляд", "color": "#95a5a6", "required_xp": 0, "reward_coins": 0},
    {"id": 2, "name": "Потерянный", "color": "#7f8c8d", "required_xp": 500, "reward_coins": 50},
    {"id": 3, "name": "Холодный", "color": "#5d6d7e", "required_xp": 1250, "reward_coins": 100},
    {"id": 4, "name": "Без сна", "color": "#34495e", "required_xp": 2250, "reward_coins": 150},
    {"id": 5, "name": "Ночной", "color": "#2c3e50", "required_xp": 3500, "reward_coins": 200},
    {"id": 6, "name": "Тихий", "color": "#566573", "required_xp": 5000, "reward_coins": 300},
    {"id": 7, "name": "Гулёныш", "color": "#616a6b", "required_xp": 6750, "reward_coins": 400},
    {"id": 8, "name": "Отрешённый", "color": "#515a5a", "required_xp": 8750, "reward_coins": 500},
    {"id": 9, "name": "Бледный", "color": "#424949", "required_xp": 11000, "reward_coins": 700},
    {"id": 10, "name": "Полумёртвый", "color": "#2e4053", "required_xp": 13500, "reward_coins": 900},
    {"id": 11, "name": "Гуль", "color": "#1c2833", "required_xp": 16250, "reward_coins": 1200},
    {"id": 12, "name": "Безэмо", "color": "#17202a", "required_xp": 19250, "reward_coins": 1500},
    {"id": 13, "name": "Пожиратель тишины", "color": "#641e16", "required_xp": 22500, "reward_coins": 2000},
    {"id": 14, "name": "Сломанный", "color": "#512e5f", "required_xp": 26000, "reward_coins": 2500},
    {"id": 15, "name": "Чёрное сердце", "color": "#1a1a1a", "required_xp": 29750, "reward_coins": 3000},
    {"id": 16, "name": "Носитель тьмы", "color": "#0d0d0d", "required_xp": 33750, "reward_coins": 4000},
    {"id": 17, "name": "Первый кошмар", "color": "#4a235a", "required_xp": 38000, "reward_coins": 5000},
    {"id": 18, "name": "Глава ночи", "color": "#1b2631", "required_xp": 42500, "reward_coins": 7000},
    {"id": 19, "name": "Король пустоты", "color": "#000000", "required_xp": 47250, "reward_coins": 10000},
    {"id": 20, "name": "Абсолютный гуль", "color": "#8b0000", "required_xp": 52250, "reward_coins": 15000},
]

class Database:
    def __init__(self):
        # Создаём папку data если её нет
        os.makedirs('data', exist_ok=True)
        self.data = self.load_data()
    
    def load_data(self):
        """Загрузить данные из файла"""
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'users': {},
            'global_stats': {
                'total_users': 0,
                'total_xp_earned': 0,
                'total_coins_earned': 0
            }
        }

    
    def save_data(self):
        """Сохранить данные в файл"""
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def get_user(self, telegram_id):
        """Получить пользователя или создать нового"""
        telegram_id = str(telegram_id)
        
        if telegram_id not in self.data['users']:
            self.data['users'][telegram_id] = {
                'telegram_id': telegram_id,
                'username': 'Unknown',
                'first_name': '',
                'xp': 0,
                'coins': 0,
                'rank_id': 1,
                'discord_id': None,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'last_daily': None,
                'last_spin': None,
                'inventory': [],
                'achievements': [],
                'games_played': 0,
                'games_won': 0,
                'total_coins_won': 0
            }
            self.data['global_stats']['total_users'] += 1
            self.save_data()
        
        return self.data['users'][telegram_id]
    
    def update_user(self, telegram_id, **kwargs):
        """Обновить данные пользователя"""
        user = self.get_user(telegram_id)
        user.update(kwargs)
        user['last_active'] = datetime.now().isoformat()
        self.save_data()
        return user
    
    def add_xp(self, telegram_id, amount):
        """Добавить XP пользователю"""
        user = self.get_user(telegram_id)
        old_rank = user['rank_id']
        user['xp'] += amount
        
        # Проверяем повышение ранга
        new_rank = self._check_rank_up(user)
        
        self.data['global_stats']['total_xp_earned'] += amount
        self.save_data()
        
        return {
            'xp': user['xp'],
            'rank_up': new_rank > old_rank,
            'old_rank': old_rank,
            'new_rank': new_rank
        }
    
    def add_coins(self, telegram_id, amount):
        """Добавить монеты пользователю"""
        user = self.get_user(telegram_id)
        user['coins'] += amount
        self.data['global_stats']['total_coins_earned'] += amount
        self.save_data()
        return user['coins']
    
    def remove_coins(self, telegram_id, amount):
        """Убрать монеты у пользователя"""
        user = self.get_user(telegram_id)
        if user['coins'] >= amount:
            user['coins'] -= amount
            self.save_data()
            return True
        return False

    
    def _check_rank_up(self, user):
        """Проверить и обновить ранг"""
        current_xp = user['xp']
        new_rank_id = 1
        
        for rank in RANKS:
            if current_xp >= rank['required_xp']:
                new_rank_id = rank['id']
        
        if new_rank_id > user['rank_id']:
            # Повышение ранга!
            user['rank_id'] = new_rank_id
            # Награда за новый ранг
            reward = RANKS[new_rank_id - 1]['reward_coins']
            user['coins'] += reward
        
        return new_rank_id
    
    def get_rank_info(self, rank_id):
        """Получить информацию о ранге"""
        if 1 <= rank_id <= len(RANKS):
            return RANKS[rank_id - 1]
        return RANKS[0]
    
    def can_claim_daily(self, telegram_id):
        """Проверить можно ли получить ежедневную награду"""
        user = self.get_user(telegram_id)
        
        if user.get('last_daily') is None:
            return True
        
        last_daily = datetime.fromisoformat(user['last_daily'])
        now = datetime.now()
        time_diff = (now - last_daily).total_seconds()
        
        # 24 часа = 86400 секунд
        return time_diff >= 86400
    
    def claim_daily(self, telegram_id, xp_reward, coins_reward):
        """Получить ежедневную награду"""
        if not self.can_claim_daily(telegram_id):
            user = self.get_user(telegram_id)
            last_daily = datetime.fromisoformat(user['last_daily'])
            time_left = 86400 - (datetime.now() - last_daily).total_seconds()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            return {
                'success': False,
                'error': f'Ты уже получил награду! Следующая через {hours}ч {minutes}м'
            }
        
        user = self.get_user(telegram_id)
        self.add_xp(telegram_id, xp_reward)
        self.add_coins(telegram_id, coins_reward)
        
        user['last_daily'] = datetime.now().isoformat()
        self.save_data()
        
        return {
            'success': True,
            'xp': xp_reward,
            'coins': coins_reward
        }
    
    def get_leaderboard(self, limit=10):
        """Получить таблицу лидеров"""
        users = list(self.data['users'].values())
        users.sort(key=lambda x: x['xp'], reverse=True)
        return users[:limit]
    
    def get_all_users(self):
        """Получить всех пользователей"""
        return list(self.data['users'].values())
    
    def link_discord(self, telegram_id, discord_id):
        """Привязать Discord ID"""
        user = self.get_user(telegram_id)
        user['discord_id'] = str(discord_id)
        self.save_data()
        return True

# Глобальный экземпляр БД
db = Database()
