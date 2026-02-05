# База данных для хранения пользователей, рангов и прогресса
import json
import os
from datetime import datetime
import hashlib
import secrets
from font_converter import convert_to_font

DATABASE_FILE = 'json/user_data.json'
ACCOUNTS_FILE = 'json/accounts.json'

# 20 рангов с буквенной системой F-S и кастомными эмодзи
RANKS = [
    # Ранг F (1-3) - Начальные
    {"id": 1, "name": "ᴩᴀнᴦ F I", "emoji": "<:F:1467727827473530931>", "color": "#95a5a6", "required_xp": 0, "reward_coins": 0, "tier": "F", "stars": 1},
    {"id": 2, "name": "ᴩᴀнᴦ F II", "emoji": "<:F:1467727827473530931>", "color": "#7f8c8d", "required_xp": 500, "reward_coins": 50, "tier": "F", "stars": 2},
    {"id": 3, "name": "ᴩᴀнᴦ F III", "emoji": "<:F:1467727827473530931>", "color": "#5d6d7e", "required_xp": 1250, "reward_coins": 100, "tier": "F", "stars": 3},
    
    # Ранг E (4-6) - Новички
    {"id": 4, "name": "ᴩᴀнᴦ E I", "emoji": "<:E:1467727807001137336>", "color": "#34495e", "required_xp": 2250, "reward_coins": 150, "tier": "E", "stars": 1},
    {"id": 5, "name": "ᴩᴀнᴦ E II", "emoji": "<:E:1467727807001137336>", "color": "#2c3e50", "required_xp": 3500, "reward_coins": 200, "tier": "E", "stars": 2},
    {"id": 6, "name": "ᴩᴀнᴦ E III", "emoji": "<:E:1467727807001137336>", "color": "#566573", "required_xp": 5000, "reward_coins": 300, "tier": "E", "stars": 3},
    
    # Ранг D (7-9) - Опытные
    {"id": 7, "name": "ᴩᴀнᴦ D I", "emoji": "<:D:1467727832456233113>", "color": "#616a6b", "required_xp": 6750, "reward_coins": 400, "tier": "D", "stars": 1},
    {"id": 8, "name": "ᴩᴀнᴦ D II", "emoji": "<:D:1467727832456233113>", "color": "#515a5a", "required_xp": 8750, "reward_coins": 500, "tier": "D", "stars": 2},
    {"id": 9, "name": "ᴩᴀнᴦ D III", "emoji": "<:D:1467727832456233113>", "color": "#424949", "required_xp": 11000, "reward_coins": 700, "tier": "D", "stars": 3},
    
    # Ранг C (10-12) - Продвинутые
    {"id": 10, "name": "ᴩᴀнᴦ C I", "emoji": "<:C:1467727811480649940>", "color": "#2e4053", "required_xp": 13500, "reward_coins": 900, "tier": "C", "stars": 1},
    {"id": 11, "name": "ᴩᴀнᴦ C II", "emoji": "<:C:1467727811480649940>", "color": "#1c2833", "required_xp": 16250, "reward_coins": 1200, "tier": "C", "stars": 2},
    {"id": 12, "name": "ᴩᴀнᴦ C III", "emoji": "<:C:1467727811480649940>", "color": "#17202a", "required_xp": 19250, "reward_coins": 1500, "tier": "C", "stars": 3},
    
    # Ранг B (13-15) - Мастера
    {"id": 13, "name": "ᴩᴀнᴦ B I", "emoji": "<:B:1467727824558231653>", "color": "#641e16", "required_xp": 22500, "reward_coins": 2000, "tier": "B", "stars": 1},
    {"id": 14, "name": "ᴩᴀнᴦ B II", "emoji": "<:B:1467727824558231653>", "color": "#512e5f", "required_xp": 26000, "reward_coins": 2500, "tier": "B", "stars": 2},
    {"id": 15, "name": "ᴩᴀнᴦ B III", "emoji": "<:B:1467727824558231653>", "color": "#1a1a1a", "required_xp": 29750, "reward_coins": 3000, "tier": "B", "stars": 3},
    
    # Ранг A (16-18) - Элита
    {"id": 16, "name": "ᴩᴀнᴦ A I", "emoji": "<:A:1467727451500187718>", "color": "#0d0d0d", "required_xp": 33750, "reward_coins": 4000, "tier": "A", "stars": 1},
    {"id": 17, "name": "ᴩᴀнᴦ A II", "emoji": "<:A:1467727451500187718>", "color": "#4a235a", "required_xp": 38000, "reward_coins": 5000, "tier": "A", "stars": 2},
    {"id": 18, "name": "ᴩᴀнᴦ A III", "emoji": "<:A:1467727451500187718>", "color": "#1b2631", "required_xp": 42500, "reward_coins": 7000, "tier": "A", "stars": 3},
    
    # Ранг S (19-20) - Легенды
    {"id": 19, "name": "ᴩᴀнᴦ S I", "emoji": "<:S:1467727794296328234>", "color": "#8b0000", "required_xp": 47250, "reward_coins": 10000, "tier": "S", "stars": 1},
    {"id": 20, "name": "ᴩᴀнᴦ S II", "emoji": "<:S:1467727794296328234>", "color": "#ff0000", "required_xp": 52250, "reward_coins": 15000, "tier": "S", "stars": 2},
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
                'bg_color': '#667eea',
                'background_url': '',
                'background_type': 'color',
                'profile_bg_color': '#667eea',
                'profile_bg_url': '',
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
            for key in ['bio', 'music_url', 'theme', 'background_color', 'bg_color', 'text_color', 'avatar_url', 'background_url', 'background_type', 'profile_bg_color', 'profile_bg_url']:
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
                'daily_streak': 0,
                'last_daily_date': None,
                'achievements': [],
                'daily_tasks': self._generate_daily_tasks(),
                'games_played': 0,
                'games_won': 0
            }
            self.save_data()
        else:
            # Добавляем новые поля для существующих пользователей
            user = self.data['users'][user_id]
            if 'daily_streak' not in user:
                user['daily_streak'] = 0
            if 'last_daily_date' not in user:
                user['last_daily_date'] = None
            if 'games_played' not in user:
                user['games_played'] = 0
            if 'games_won' not in user:
                user['games_won'] = 0
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
    
    def save_user(self, user_id, user_data):
        """Сохранить данные пользователя (альтернативный метод)"""
        user_id = str(user_id)
        self.data['users'][user_id] = user_data
        self.data['users'][user_id]['last_active'] = datetime.now().isoformat()
        
        # Проверяем повышение ранга
        self._check_rank_up(self.data['users'][user_id])
        
        self.save_data()
        return self.data['users'][user_id]
    
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
    
    def check_rank_up(self, user):
        """Публичный метод для проверки повышения ранга"""
        return self._check_rank_up(user)
    
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
    
    def get_all_users(self):
        """Получить всех пользователей"""
        return self.data.get('users', {})
    
    def get_all_accounts(self):
        """Получить все аккаунты"""
        all_accounts = list(self.accounts.get('accounts', {}).values())
        # Сортируем по дате создания (новые первые)
        all_accounts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return all_accounts

# Глобальный экземпляр базы данных
db = Database()
