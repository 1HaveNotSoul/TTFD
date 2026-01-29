# База данных для хранения пользователей, рангов и прогресса
import json
import os
from datetime import datetime
import hashlib
import secrets

DATABASE_FILE = 'user_data.json'
ACCOUNTS_FILE = 'accounts.json'

# 20 рангов с требованиями
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
        self.data = self.load_data()
        self.accounts = self.load_accounts()
    
    def load_data(self):
        """Загрузить данные из файла"""
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'users': {}, 'global_stats': {'total_clicks': 0, 'total_tasks_completed': 0}}
    
    def load_accounts(self):
        """Загрузить аккаунты"""
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'accounts': {}, 'sessions': {}}
    
    def save_data(self):
        """Сохранить данные в файл"""
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def save_accounts(self):
        """Сохранить аккаунты"""
        with open(ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, indent=2, ensure_ascii=False)
    
    # ==================== АККАУНТЫ ====================
    
    def hash_password(self, password):
        """Хешировать пароль"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_account(self, email, username, password, display_name):
        """Создать аккаунт"""
        # Проверка существования
        for acc in self.accounts['accounts'].values():
            if acc['email'] == email:
                return {'success': False, 'error': 'Email уже используется'}
            if acc['username'] == username:
                return {'success': False, 'error': 'Логин уже занят'}
        
        account_id = str(len(self.accounts['accounts']) + 1)
        self.accounts['accounts'][account_id] = {
            'id': account_id,
            'email': email,
            'username': username,
            'password': self.hash_password(password),
            'display_name': display_name,
            'discord_id': None,
            'created_at': datetime.now().isoformat(),
            'profile': {
                'bio': '',
                'music_url': '',
                'theme': 'default',
                'background_color': '#667eea',
                'text_color': '#ffffff',
                'avatar_url': '',
                'social_links': {}
            }
        }
        self.save_accounts()
        return {'success': True, 'account_id': account_id}
    
    def login(self, username, password):
        """Войти в аккаунт"""
        password_hash = self.hash_password(password)
        
        for acc in self.accounts['accounts'].values():
            if acc['username'] == username and acc['password'] == password_hash:
                # Создаём сессию
                session_token = secrets.token_urlsafe(32)
                self.accounts['sessions'][session_token] = {
                    'account_id': acc['id'],
                    'created_at': datetime.now().isoformat()
                }
                self.save_accounts()
                return {'success': True, 'token': session_token, 'account': acc}
        
        return {'success': False, 'error': 'Неверный логин или пароль'}
    
    def get_account_by_token(self, token):
        """Получить аккаунт по токену сессии"""
        if token in self.accounts['sessions']:
            account_id = self.accounts['sessions'][token]['account_id']
            return self.accounts['accounts'].get(account_id)
        return None
    
    def get_account_by_username(self, username):
        """Получить аккаунт по username"""
        for acc in self.accounts['accounts'].values():
            if acc['username'] == username:
                return acc
        return None
    
    def update_profile(self, account_id, **kwargs):
        """Обновить профиль"""
        if account_id in self.accounts['accounts']:
            account = self.accounts['accounts'][account_id]
            
            # Обновляем основные поля
            if 'display_name' in kwargs:
                account['display_name'] = kwargs['display_name']
            if 'email' in kwargs:
                # Проверка уникальности email
                for acc in self.accounts['accounts'].values():
                    if acc['id'] != account_id and acc['email'] == kwargs['email']:
                        return {'success': False, 'error': 'Email уже используется'}
                account['email'] = kwargs['email']
            
            # Обновляем профиль
            for key in ['bio', 'music_url', 'theme', 'background_color', 'text_color', 'avatar_url']:
                if key in kwargs:
                    account['profile'][key] = kwargs[key]
            
            self.save_accounts()
            return {'success': True, 'account': account}
        
        return {'success': False, 'error': 'Аккаунт не найден'}
    
    def change_password(self, account_id, old_password, new_password):
        """Сменить пароль"""
        if account_id in self.accounts['accounts']:
            account = self.accounts['accounts'][account_id]
            
            if account['password'] == self.hash_password(old_password):
                account['password'] = self.hash_password(new_password)
                self.save_accounts()
                return {'success': True}
            else:
                return {'success': False, 'error': 'Неверный старый пароль'}
        
        return {'success': False, 'error': 'Аккаунт не найден'}
    
    def link_discord(self, account_id, discord_id):
        """Привязать Discord ID к аккаунту"""
        if account_id in self.accounts['accounts']:
            self.accounts['accounts'][account_id]['discord_id'] = discord_id
            self.save_accounts()
            return {'success': True}
        return {'success': False, 'error': 'Аккаунт не найден'}
    
    def logout(self, token):
        """Выйти из аккаунта"""
        if token in self.accounts['sessions']:
            del self.accounts['sessions'][token]
            self.save_accounts()
            return {'success': True}
        return {'success': False}
    
    def get_user(self, user_id):
        """Получить данные пользователя"""
        user_id = str(user_id)
        if user_id not in self.data['users']:
            self.data['users'][user_id] = {
                'id': user_id,
                'username': 'Unknown',
                'xp': 0,
                'coins': 0,
                'clicks': 0,
                'tasks_completed': 0,
                'rank_id': 1,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                'last_daily': None,
                'achievements': [],
                'daily_tasks': self._generate_daily_tasks()
            }
            self.save_data()
        return self.data['users'][user_id]
    
    def update_user(self, user_id, **kwargs):
        """Обновить данные пользователя"""
        user = self.get_user(user_id)
        user.update(kwargs)
        user['last_active'] = datetime.now().isoformat()
        
        # Проверяем повышение ранга
        self._check_rank_up(user)
        
        self.save_data()
        return user
    
    def add_xp(self, user_id, amount):
        """Добавить опыт пользователю"""
        user = self.get_user(user_id)
        old_rank = user['rank_id']
        user['xp'] += amount
        
        # Проверяем повышение ранга
        new_rank = self._check_rank_up(user)
        
        self.save_data()
        
        # Возвращаем информацию о повышении
        return {
            'xp': user['xp'],
            'rank_up': new_rank > old_rank,
            'old_rank': old_rank,
            'new_rank': new_rank
        }
    
    def add_coins(self, user_id, amount):
        """Добавить монеты пользователю"""
        user = self.get_user(user_id)
        user['coins'] += amount
        self.save_data()
        return user['coins']
    
    def _check_rank_up(self, user):
        """Проверить и обновить ранг пользователя"""
        current_xp = user['xp']
        new_rank_id = 1
        
        for rank in RANKS:
            if current_xp >= rank['required_xp']:
                new_rank_id = rank['id']
        
        if new_rank_id > user['rank_id']:
            # Повышение ранга!
            user['rank_id'] = new_rank_id
            # Даём награду за новый ранг
            reward = RANKS[new_rank_id - 1]['reward_coins']
            user['coins'] += reward
        
        return new_rank_id
    
    def _generate_daily_tasks(self):
        """Генерировать ежедневные задания"""
        return [
            {'id': 1, 'name': 'Сделай 100 кликов', 'target': 100, 'progress': 0, 'reward_xp': 50, 'reward_coins': 25, 'completed': False},
            {'id': 2, 'name': 'Сделай 500 кликов', 'target': 500, 'progress': 0, 'reward_xp': 200, 'reward_coins': 100, 'completed': False},
            {'id': 3, 'name': 'Сделай 1000 кликов', 'target': 1000, 'progress': 0, 'reward_xp': 500, 'reward_coins': 250, 'completed': False},
            {'id': 4, 'name': 'Будь активен 5 минут', 'target': 300, 'progress': 0, 'reward_xp': 100, 'reward_coins': 50, 'completed': False},
        ]
    
    def complete_task(self, user_id, task_id):
        """Завершить задание"""
        user = self.get_user(user_id)
        
        for task in user['daily_tasks']:
            if task['id'] == task_id and not task['completed']:
                # Проверяем, выполнено ли задание
                if task['progress'] < task['target']:
                    return {'success': False, 'error': 'Задание ещё не выполнено'}
                
                task['completed'] = True
                user['tasks_completed'] += 1
                user['xp'] += task['reward_xp']
                user['coins'] += task['reward_coins']
                
                self.data['global_stats']['total_tasks_completed'] += 1
                self._check_rank_up(user)
                self.save_data()
                
                return {'success': True, 'task': task}
        
        return {'success': False, 'error': 'Task not found or already completed'}
    
    def get_leaderboard(self, limit=10):
        """Получить таблицу лидеров"""
        users = list(self.data['users'].values())
        users.sort(key=lambda x: x['xp'], reverse=True)
        return users[:limit]
    
    def get_rank_info(self, rank_id):
        """Получить информацию о ранге"""
        if 1 <= rank_id <= len(RANKS):
            return RANKS[rank_id - 1]
        return RANKS[0]
    
    def can_claim_daily(self, user_id):
        """Проверить можно ли получить ежедневную награду"""
        user = self.get_user(user_id)
        
        if user.get('last_daily') is None:
            return True
        
        last_daily = datetime.fromisoformat(user['last_daily'])
        now = datetime.now()
        time_diff = (now - last_daily).total_seconds()
        
        # 24 часа = 86400 секунд
        return time_diff >= 86400
    
    def claim_daily(self, user_id):
        """Получить ежедневную награду"""
        if not self.can_claim_daily(user_id):
            user = self.get_user(user_id)
            last_daily = datetime.fromisoformat(user['last_daily'])
            time_left = 86400 - (datetime.now() - last_daily).total_seconds()
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            return {
                'success': False,
                'error': f'Ты уже получил награду! Следующая через {hours}ч {minutes}м'
            }
        
        user = self.get_user(user_id)
        reward_xp = 100
        reward_coins = 50
        
        self.add_xp(user_id, reward_xp)
        self.add_coins(user_id, reward_coins)
        
        user['last_daily'] = datetime.now().isoformat()
        self.save_data()
        
        return {
            'success': True,
            'xp': reward_xp,
            'coins': reward_coins
        }
    
    def get_all_ranks(self):
        """Получить все ранги"""
        return RANKS

# Глобальный экземпляр базы данных
db = Database()
