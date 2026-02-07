# База данных PostgreSQL для Discord бота
import os
from datetime import datetime, timedelta
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

# 20 рангов с буквенной системой F-S
RANKS = [
    # Ранг F (1-3)
    {"id": 1, "name": "ᴩᴀнᴦ F I", "emoji": "<:F:1467727827473530931>", "color": "#95a5a6", "required_xp": 0, "reward_coins": 0, "tier": "F", "stars": 1},
    {"id": 2, "name": "ᴩᴀнᴦ F II", "emoji": "<:F:1467727827473530931>", "color": "#7f8c8d", "required_xp": 500, "reward_coins": 50, "tier": "F", "stars": 2},
    {"id": 3, "name": "ᴩᴀнᴦ F III", "emoji": "<:F:1467727827473530931>", "color": "#5d6d7e", "required_xp": 1250, "reward_coins": 100, "tier": "F", "stars": 3},
    
    # Ранг E (4-6)
    {"id": 4, "name": "ᴩᴀнᴦ E I", "emoji": "<:E:1467727807001137336>", "color": "#34495e", "required_xp": 2250, "reward_coins": 150, "tier": "E", "stars": 1},
    {"id": 5, "name": "ᴩᴀнᴦ E II", "emoji": "<:E:1467727807001137336>", "color": "#2c3e50", "required_xp": 3500, "reward_coins": 200, "tier": "E", "stars": 2},
    {"id": 6, "name": "ᴩᴀнᴦ E III", "emoji": "<:E:1467727807001137336>", "color": "#566573", "required_xp": 5000, "reward_coins": 300, "tier": "E", "stars": 3},
    
    # Ранг D (7-9)
    {"id": 7, "name": "ᴩᴀнᴦ D I", "emoji": "<:D:1467727832456233113>", "color": "#616a6b", "required_xp": 6750, "reward_coins": 400, "tier": "D", "stars": 1},
    {"id": 8, "name": "ᴩᴀнᴦ D II", "emoji": "<:D:1467727832456233113>", "color": "#515a5a", "required_xp": 8750, "reward_coins": 500, "tier": "D", "stars": 2},
    {"id": 9, "name": "ᴩᴀнᴦ D III", "emoji": "<:D:1467727832456233113>", "color": "#424949", "required_xp": 11000, "reward_coins": 700, "tier": "D", "stars": 3},
    
    # Ранг C (10-12)
    {"id": 10, "name": "ᴩᴀнᴦ C I", "emoji": "<:C:1467727811480649940>", "color": "#2e4053", "required_xp": 13500, "reward_coins": 900, "tier": "C", "stars": 1},
    {"id": 11, "name": "ᴩᴀнᴦ C II", "emoji": "<:C:1467727811480649940>", "color": "#1c2833", "required_xp": 16250, "reward_coins": 1200, "tier": "C", "stars": 2},
    {"id": 12, "name": "ᴩᴀнᴦ C III", "emoji": "<:C:1467727811480649940>", "color": "#17202a", "required_xp": 19250, "reward_coins": 1500, "tier": "C", "stars": 3},
    
    # Ранг B (13-15)
    {"id": 13, "name": "ᴩᴀнᴦ B I", "emoji": "<:B:1467727824558231653>", "color": "#641e16", "required_xp": 22500, "reward_coins": 2000, "tier": "B", "stars": 1},
    {"id": 14, "name": "ᴩᴀнᴦ B II", "emoji": "<:B:1467727824558231653>", "color": "#512e5f", "required_xp": 26000, "reward_coins": 2500, "tier": "B", "stars": 2},
    {"id": 15, "name": "ᴩᴀнᴦ B III", "emoji": "<:B:1467727824558231653>", "color": "#1a1a1a", "required_xp": 29750, "reward_coins": 3000, "tier": "B", "stars": 3},
    
    # Ранг A (16-18)
    {"id": 16, "name": "ᴩᴀнᴦ A I", "emoji": "<:A:1467727451500187718>", "color": "#0d0d0d", "required_xp": 33750, "reward_coins": 4000, "tier": "A", "stars": 1},
    {"id": 17, "name": "ᴩᴀнᴦ A II", "emoji": "<:A:1467727451500187718>", "color": "#4a235a", "required_xp": 38000, "reward_coins": 5000, "tier": "A", "stars": 2},
    {"id": 18, "name": "ᴩᴀнᴦ A III", "emoji": "<:A:1467727451500187718>", "color": "#1b2631", "required_xp": 42500, "reward_coins": 7000, "tier": "A", "stars": 3},
    
    # Ранг S (19-20)
    {"id": 19, "name": "ᴩᴀнᴦ S I", "emoji": "<:S:1467727794296328234>", "color": "#8b0000", "required_xp": 47250, "reward_coins": 10000, "tier": "S", "stars": 1},
    {"id": 20, "name": "ᴩᴀнᴦ S II", "emoji": "<:S:1467727794296328234>", "color": "#ff0000", "required_xp": 52250, "reward_coins": 15000, "tier": "S", "stars": 2},
]

class PostgresDatabase:
    def __init__(self):
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 не установлен")
        
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL не установлен")
        
        # Render/Railway используют postgres://, но psycopg2 требует postgresql://
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
        
        # Таблица пользователей Discord
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
                daily_streak INTEGER DEFAULT 0,
                last_daily_date DATE,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                last_dice TIMESTAMP,
                last_coinflip TIMESTAMP,
                last_work TIMESTAMP,
                daily_tasks JSONB DEFAULT '[]'::jsonb,
                achievements JSONB DEFAULT '[]'::jsonb,
                inventory JSONB DEFAULT '[]'::jsonb,
                active_boosts JSONB DEFAULT '[]'::jsonb,
                game_stats JSONB DEFAULT '{}'::jsonb
            )
        """)
        
        # Таблица голосовой активности
        cur.execute("""
            CREATE TABLE IF NOT EXISTS voice_activity (
                user_id TEXT PRIMARY KEY,
                total_time INTEGER DEFAULT 0,
                last_join TIMESTAMP,
                sessions JSONB DEFAULT '[]'::jsonb
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
        
        # Вставляем начальную статистику
        cur.execute("INSERT INTO global_stats (id) VALUES (1) ON CONFLICT DO NOTHING")
        
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Таблицы PostgreSQL инициализированы")
    
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
        
        # Преобразуем в dict и парсим JSON поля
        user_dict = dict(user)
        for json_field in ['daily_tasks', 'achievements', 'inventory', 'active_boosts', 'game_stats']:
            if json_field in user_dict and user_dict[json_field]:
                if isinstance(user_dict[json_field], str):
                    user_dict[json_field] = json.loads(user_dict[json_field])
        
        # Добавляем поля для совместимости
        if 'daily_streak' not in user_dict:
            user_dict['daily_streak'] = 0
        if 'last_daily_date' not in user_dict:
            user_dict['last_daily_date'] = None
        
        return user_dict
    
    def save_user(self, user_id, user_data):
        """Сохранить пользователя"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        # Подготавливаем JSON поля
        for json_field in ['daily_tasks', 'achievements', 'inventory', 'active_boosts', 'game_stats']:
            if json_field in user_data and not isinstance(user_data[json_field], str):
                user_data[json_field] = json.dumps(user_data[json_field])
        
        # Формируем UPDATE запрос
        fields = []
        values = []
        for key, value in user_data.items():
            if key != 'id':
                fields.append(f"{key} = %s")
                values.append(value)
        
        fields.append("last_active = CURRENT_TIMESTAMP")
        values.append(str(user_id))
        
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
        cur.execute(query, values)
        
        # Проверяем повышение ранга
        cur.execute("SELECT * FROM users WHERE id = %s", (str(user_id),))
        updated_user = cur.fetchone()
        self._check_rank_up_postgres(cur, dict(updated_user))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return self.get_user(user_id)
    
    def _check_rank_up_postgres(self, cur, user):
        """Проверить повышение ранга (для PostgreSQL)"""
        current_xp = user['xp']
        new_rank_id = 1
        
        for rank in RANKS:
            if current_xp >= rank['required_xp']:
                new_rank_id = rank['id']
        
        if new_rank_id > user['rank_id']:
            # Повышение ранга!
            reward = RANKS[new_rank_id - 1]['reward_coins']
            cur.execute("""
                UPDATE users 
                SET rank_id = %s, coins = coins + %s 
                WHERE id = %s
            """, (new_rank_id, reward, user['id']))
    
    def check_rank_up(self, user):
        """Проверить повышение ранга"""
        current_xp = user['xp']
        new_rank_id = 1
        
        for rank in RANKS:
            if current_xp >= rank['required_xp']:
                new_rank_id = rank['id']
        
        if new_rank_id > user['rank_id']:
            reward = RANKS[new_rank_id - 1]['reward_coins']
            user['rank_id'] = new_rank_id
            user['coins'] += reward
        
        return new_rank_id
    
    def add_xp(self, user_id, amount):
        """Добавить XP"""
        user = self.get_user(user_id)
        old_rank = user['rank_id']
        user['xp'] += amount
        
        new_rank = self.check_rank_up(user)
        self.save_user(user_id, user)
        
        return {
            'xp': user['xp'],
            'rank_up': new_rank > old_rank,
            'old_rank': old_rank,
            'new_rank': new_rank
        }
    
    def add_coins(self, user_id, amount):
        """Добавить монеты"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("UPDATE users SET coins = coins + %s WHERE id = %s RETURNING coins", (amount, str(user_id)))
        result = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        return result['coins'] if result else 0
    
    def _generate_daily_tasks(self):
        """Генерировать задания"""
        return [
            {'id': 1, 'name': 'Сделай 100 кликов', 'target': 100, 'progress': 0, 'reward_xp': 50, 'reward_coins': 25, 'completed': False},
            {'id': 2, 'name': 'Сделай 500 кликов', 'target': 500, 'progress': 0, 'reward_xp': 200, 'reward_coins': 100, 'completed': False},
            {'id': 3, 'name': 'Сделай 1000 кликов', 'target': 1000, 'progress': 0, 'reward_xp': 500, 'reward_coins': 250, 'completed': False},
            {'id': 4, 'name': 'Будь активен 5 минут', 'target': 300, 'progress': 0, 'reward_xp': 100, 'reward_coins': 50, 'completed': False},
        ]
    
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
    
    def get_all_users(self):
        """Получить всех пользователей"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        
        cur.close()
        conn.close()
        
        result = {}
        for user in users:
            user_dict = dict(user)
            # Парсим JSON поля
            for json_field in ['daily_tasks', 'achievements', 'inventory', 'active_boosts', 'game_stats']:
                if json_field in user_dict and user_dict[json_field]:
                    if isinstance(user_dict[json_field], str):
                        user_dict[json_field] = json.loads(user_dict[json_field])
            result[user_dict['id']] = user_dict
        
        return result
    
    # Методы для голосовой активности
    def get_voice_data(self, user_id):
        """Получить данные голосовой активности"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM voice_activity WHERE user_id = %s", (str(user_id),))
        data = cur.fetchone()
        
        if not data:
            cur.execute("""
                INSERT INTO voice_activity (user_id, total_time, sessions)
                VALUES (%s, 0, %s)
                RETURNING *
            """, (str(user_id), json.dumps([])))
            data = cur.fetchone()
            conn.commit()
        
        cur.close()
        conn.close()
        
        result = dict(data)
        if 'sessions' in result and isinstance(result['sessions'], str):
            result['sessions'] = json.loads(result['sessions'])
        return result
    
    def save_voice_data(self, user_id, voice_data):
        """Сохранить данные голосовой активности"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        if 'sessions' in voice_data and not isinstance(voice_data['sessions'], str):
            voice_data['sessions'] = json.dumps(voice_data['sessions'])
        
        cur.execute("""
            UPDATE voice_activity 
            SET total_time = %s, last_join = %s, sessions = %s
            WHERE user_id = %s
        """, (voice_data['total_time'], voice_data.get('last_join'), voice_data['sessions'], str(user_id)))
        
        conn.commit()
        cur.close()
        conn.close()

# Создаём экземпляр
try:
    if os.getenv('DATABASE_URL') and PSYCOPG2_AVAILABLE:
        db = PostgresDatabase()
        print("✅ Discord Bot: Используется PostgreSQL")
    else:
        raise ValueError("PostgreSQL не настроен")
except Exception as e:
    print(f"⚠️ PostgreSQL недоступен: {e}")
    print("⚠️ Используется JSON файл")
    from database import db
