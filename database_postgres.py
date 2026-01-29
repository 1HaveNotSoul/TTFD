# База данных PostgreSQL для постоянного хранения
import os
from datetime import datetime
import hashlib
import secrets
import json

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("⚠️ psycopg2 не установлен, PostgreSQL недоступен")

# Ранги (те же самые)
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

class PostgresDatabase:
    def __init__(self):
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 не установлен")
        
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL не установлен")
        
        # Render использует postgres://, но psycopg2 требует postgresql://
        if self.database_url.startswith('postgres://'):
            self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
        
        self.init_tables()
    
    def get_connection(self):
        """Получить подключение к БД"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)
    
    def init_tables(self):
        """Создать таблицы если их нет"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        # Таблица пользователей
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT,
                xp INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                tasks_completed INTEGER DEFAULT 0,
                rank_id INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_daily TIMESTAMP,
                daily_tasks JSONB DEFAULT '[]'::jsonb
            )
        """)
        
        # Таблица аккаунтов
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE,
                username TEXT UNIQUE,
                password TEXT,
                display_name TEXT,
                discord_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                profile JSONB DEFAULT '{}'::jsonb
            )
        """)
        
        # Таблица сессий
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                account_id INTEGER REFERENCES accounts(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Глобальная статистика
        cur.execute("""
            CREATE TABLE IF NOT EXISTS global_stats (
                id INTEGER PRIMARY KEY DEFAULT 1,
                total_clicks BIGINT DEFAULT 0,
                total_tasks_completed BIGINT DEFAULT 0
            )
        """)
        
        # Вставляем начальную статистику если её нет
        cur.execute("INSERT INTO global_stats (id) VALUES (1) ON CONFLICT DO NOTHING")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Таблицы PostgreSQL инициализированы")
    
    def hash_password(self, password):
        """Хешировать пароль"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def get_user(self, user_id):
        """Получить пользователя"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE id = %s", (str(user_id),))
        user = cur.fetchone()
        
        if not user:
            # Создаём нового пользователя
            daily_tasks = self._generate_daily_tasks()
            cur.execute("""
                INSERT INTO users (id, username, daily_tasks)
                VALUES (%s, %s, %s)
                RETURNING *
            """, (str(user_id), 'Unknown', json.dumps(daily_tasks)))
            user = cur.fetchone()
            conn.commit()
        
        cur.close()
        conn.close()
        
        # Преобразуем в dict
        user_dict = dict(user)
        user_dict['daily_tasks'] = json.loads(user_dict['daily_tasks']) if isinstance(user_dict['daily_tasks'], str) else user_dict['daily_tasks']
        return user_dict
    
    def update_user(self, user_id, **kwargs):
        """Обновить пользователя"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        # Формируем SET часть запроса
        set_parts = []
        values = []
        for key, value in kwargs.items():
            if key == 'daily_tasks':
                set_parts.append(f"{key} = %s")
                values.append(json.dumps(value))
            else:
                set_parts.append(f"{key} = %s")
                values.append(value)
        
        set_parts.append("last_active = CURRENT_TIMESTAMP")
        values.append(str(user_id))
        
        query = f"UPDATE users SET {', '.join(set_parts)} WHERE id = %s RETURNING *"
        cur.execute(query, values)
        user = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        return dict(user) if user else None
    
    def add_xp(self, user_id, amount):
        """Добавить XP"""
        user = self.get_user(user_id)
        old_rank = user['rank_id']
        new_xp = user['xp'] + amount
        
        # Проверяем повышение ранга
        new_rank = 1
        for rank in RANKS:
            if new_xp >= rank['required_xp']:
                new_rank = rank['id']
        
        # Награда за повышение ранга
        coins_reward = 0
        if new_rank > old_rank:
            coins_reward = RANKS[new_rank - 1]['reward_coins']
        
        # Обновляем пользователя
        self.update_user(user_id, 
            xp=new_xp, 
            rank_id=new_rank,
            coins=user['coins'] + coins_reward
        )
        
        return {
            'xp': new_xp,
            'rank_up': new_rank > old_rank,
            'old_rank': old_rank,
            'new_rank': new_rank
        }
    
    def _generate_daily_tasks(self):
        """Генерировать задания"""
        return [
            {'id': 1, 'name': 'Сделай 100 кликов', 'target': 100, 'progress': 0, 'reward_xp': 50, 'reward_coins': 25, 'completed': False},
            {'id': 2, 'name': 'Сделай 500 кликов', 'target': 500, 'progress': 0, 'reward_xp': 200, 'reward_coins': 100, 'completed': False},
            {'id': 3, 'name': 'Сделай 1000 кликов', 'target': 1000, 'progress': 0, 'reward_xp': 500, 'reward_coins': 250, 'completed': False},
            {'id': 4, 'name': 'Будь активен 5 минут', 'target': 300, 'progress': 0, 'reward_xp': 100, 'reward_coins': 50, 'completed': False},
        ]
    
    def complete_task(self, user_id, task_id):
        """Завершить задание"""
        user = self.get_user(user_id)
        daily_tasks = user['daily_tasks']
        
        for task in daily_tasks:
            if task['id'] == task_id and not task['completed']:
                if task['progress'] < task['target']:
                    return {'success': False, 'error': 'Задание ещё не выполнено'}
                
                task['completed'] = True
                
                # Обновляем пользователя
                self.update_user(user_id,
                    daily_tasks=daily_tasks,
                    tasks_completed=user['tasks_completed'] + 1,
                    xp=user['xp'] + task['reward_xp'],
                    coins=user['coins'] + task['reward_coins']
                )
                
                # Обновляем глобальную статистику
                conn = self.get_connection()
                cur = conn.cursor()
                cur.execute("UPDATE global_stats SET total_tasks_completed = total_tasks_completed + 1 WHERE id = 1")
                conn.commit()
                cur.close()
                conn.close()
                
                return {'success': True, 'task': task}
        
        return {'success': False, 'error': 'Task not found or already completed'}
    
    def get_leaderboard(self, limit=10):
        """Получить таблицу лидеров"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users ORDER BY xp DESC LIMIT %s", (limit,))
        users = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [dict(u) for u in users]
    
    def get_rank_info(self, rank_id):
        """Получить информацию о ранге"""
        if 1 <= rank_id <= len(RANKS):
            return RANKS[rank_id - 1]
        return RANKS[0]
    
    def get_all_ranks(self):
        """Получить все ранги"""
        return RANKS
    
    # Методы для аккаунтов (аналогично JSON версии)
    def create_account(self, email, username, password, display_name):
        """Создать аккаунт"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO accounts (email, username, password, display_name, profile)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (email, username, self.hash_password(password), display_name, json.dumps({
                'bio': '', 'music_url': '', 'theme': 'default',
                'background_color': '#667eea', 'text_color': '#ffffff',
                'avatar_url': '', 'social_links': {}
            })))
            
            account_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()
            
            return {'success': True, 'account_id': account_id}
        except psycopg2.IntegrityError as e:
            conn.rollback()
            cur.close()
            conn.close()
            
            if 'email' in str(e):
                return {'success': False, 'error': 'Email уже используется'}
            elif 'username' in str(e):
                return {'success': False, 'error': 'Логин уже занят'}
            return {'success': False, 'error': str(e)}
    
    def login(self, username, password):
        """Войти"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        password_hash = self.hash_password(password)
        cur.execute("SELECT * FROM accounts WHERE username = %s AND password = %s", (username, password_hash))
        account = cur.fetchone()
        
        if account:
            # Создаём сессию
            token = secrets.token_urlsafe(32)
            cur.execute("INSERT INTO sessions (token, account_id) VALUES (%s, %s)", (token, account['id']))
            conn.commit()
            
            cur.close()
            conn.close()
            
            return {'success': True, 'token': token, 'account': dict(account)}
        
        cur.close()
        conn.close()
        return {'success': False, 'error': 'Неверный логин или пароль'}

# Создаём экземпляр
try:
    if os.getenv('DATABASE_URL') and PSYCOPG2_AVAILABLE:
        db = PostgresDatabase()
        print("✅ Используется PostgreSQL")
    else:
        raise ValueError("PostgreSQL не настроен")
except Exception as e:
    print(f"⚠️ PostgreSQL недоступен: {e}")
    print("⚠️ Используется JSON файл")
    from database import db
