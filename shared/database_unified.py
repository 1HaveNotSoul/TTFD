"""
Unified Database - Единая база данных для всех платформ
PostgreSQL с поддержкой Telegram, Discord и Website
"""
import os
import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from models import UnifiedUser, PlatformLink, CrossPlatformEvent, UNIFIED_RANKS, calculate_rank_by_xp

logger = logging.getLogger(__name__)


class UnifiedDatabase:
    """Единая база данных для всех платформ"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Подключиться к БД"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ Подключение к unified БД установлено")
            await self.init_tables()
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise
    
    async def disconnect(self):
        """Отключиться от БД"""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Отключение от unified БД")
    
    async def init_tables(self):
        """Создать таблицы если их нет"""
        async with self.pool.acquire() as conn:
            # Таблица унифицированных пользователей
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS unified_users (
                    id SERIAL PRIMARY KEY,
                    
                    -- Привязки платформ
                    telegram_id TEXT UNIQUE,
                    discord_id TEXT UNIQUE,
                    website_email TEXT UNIQUE,
                    
                    -- Основная информация
                    username TEXT NOT NULL DEFAULT 'Unknown',
                    display_name TEXT NOT NULL DEFAULT 'Unknown',
                    
                    -- Игровые данные
                    xp INTEGER NOT NULL DEFAULT 0,
                    coins INTEGER NOT NULL DEFAULT 0,
                    rank_id INTEGER NOT NULL DEFAULT 1,
                    
                    -- Статистика
                    games_played INTEGER NOT NULL DEFAULT 0,
                    games_won INTEGER NOT NULL DEFAULT 0,
                    total_voice_time INTEGER NOT NULL DEFAULT 0,
                    messages_sent INTEGER NOT NULL DEFAULT 0,
                    
                    -- Достижения и прогресс
                    achievements JSONB DEFAULT '[]'::jsonb,
                    current_season_xp INTEGER NOT NULL DEFAULT 0,
                    season_rank INTEGER NOT NULL DEFAULT 0,
                    daily_streak INTEGER NOT NULL DEFAULT 0,
                    
                    -- Метаданные
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_daily TIMESTAMP,
                    
                    -- Привязки
                    platforms JSONB DEFAULT '[]'::jsonb,
                    primary_platform TEXT NOT NULL DEFAULT 'telegram',
                    
                    -- Индексы
                    CONSTRAINT check_at_least_one_platform CHECK (
                        telegram_id IS NOT NULL OR 
                        discord_id IS NOT NULL OR 
                        website_email IS NOT NULL
                    )
                );
                
                CREATE INDEX IF NOT EXISTS idx_unified_users_telegram ON unified_users(telegram_id);
                CREATE INDEX IF NOT EXISTS idx_unified_users_discord ON unified_users(discord_id);
                CREATE INDEX IF NOT EXISTS idx_unified_users_website ON unified_users(website_email);
                CREATE INDEX IF NOT EXISTS idx_unified_users_xp ON unified_users(xp DESC);
            """)
            
            # Таблица событий синхронизации
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cross_platform_events (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id INTEGER NOT NULL REFERENCES unified_users(id) ON DELETE CASCADE,
                    
                    -- Тип и источник
                    event_type TEXT NOT NULL,
                    source_platform TEXT NOT NULL,
                    
                    -- Данные
                    data JSONB NOT NULL,
                    
                    -- Статус
                    processed BOOLEAN NOT NULL DEFAULT FALSE,
                    processed_at TIMESTAMP,
                    
                    -- Метаданные
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    
                    INDEX idx_cross_platform_events_user (user_id),
                    INDEX idx_cross_platform_events_processed (processed),
                    INDEX idx_cross_platform_events_created (created_at)
                );
            """)
            
            logger.info("✅ Таблицы unified БД инициализированы")
    
    # ========================================================================
    # ПОЛЬЗОВАТЕЛИ
    # ========================================================================
    
    async def get_user_by_telegram(self, telegram_id: str) -> Optional[UnifiedUser]:
        """Получить пользователя по Telegram ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM unified_users WHERE telegram_id = $1",
                telegram_id
            )
            return self._row_to_user(row) if row else None
    
    async def get_user_by_discord(self, discord_id: str) -> Optional[UnifiedUser]:
        """Получить пользователя по Discord ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM unified_users WHERE discord_id = $1",
                discord_id
            )
            return self._row_to_user(row) if row else None
    
    async def get_user_by_website(self, website_email: str) -> Optional[UnifiedUser]:
        """Получить пользователя по Website email"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM unified_users WHERE website_email = $1",
                website_email
            )
            return self._row_to_user(row) if row else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[UnifiedUser]:
        """Получить пользователя по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM unified_users WHERE id = $1",
                user_id
            )
            return self._row_to_user(row) if row else None
    
    async def create_user(
        self,
        telegram_id: Optional[str] = None,
        discord_id: Optional[str] = None,
        website_email: Optional[str] = None,
        username: str = "Unknown",
        display_name: str = "Unknown",
        primary_platform: str = "telegram"
    ) -> UnifiedUser:
        """Создать нового пользователя"""
        import json
        
        platforms = []
        if telegram_id:
            platforms.append("telegram")
        if discord_id:
            platforms.append("discord")
        if website_email:
            platforms.append("website")
        
        # Конвертируем список в JSON строку для PostgreSQL
        platforms_json = json.dumps(platforms)
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO unified_users (
                    telegram_id, discord_id, website_email,
                    username, display_name, platforms, primary_platform
                )
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
                RETURNING *
            """, telegram_id, discord_id, website_email, username, display_name, platforms_json, primary_platform)
            
            user = self._row_to_user(row)
            logger.info(f"✅ Создан пользователь: id={user.id}, platforms={platforms}")
            return user
    
    async def link_telegram(self, user_id: int, telegram_id: str) -> bool:
        """Привязать Telegram к существующему пользователю"""
        async with self.pool.acquire() as conn:
            # Проверяем что telegram_id не занят
            existing = await conn.fetchrow(
                "SELECT id FROM unified_users WHERE telegram_id = $1",
                telegram_id
            )
            if existing:
                logger.warning(f"⚠️  Telegram ID {telegram_id} уже привязан")
                return False
            
            # Обновляем пользователя
            await conn.execute("""
                UPDATE unified_users
                SET telegram_id = $1,
                    platforms = platforms || '["telegram"]'::jsonb
                WHERE id = $2 AND telegram_id IS NULL
            """, telegram_id, user_id)
            
            logger.info(f"✅ Telegram привязан: user_id={user_id}, telegram_id={telegram_id}")
            return True
    
    async def link_discord(self, user_id: int, discord_id: str) -> bool:
        """Привязать Discord к существующему пользователю"""
        async with self.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM unified_users WHERE discord_id = $1",
                discord_id
            )
            if existing:
                logger.warning(f"⚠️  Discord ID {discord_id} уже привязан")
                return False
            
            await conn.execute("""
                UPDATE unified_users
                SET discord_id = $1,
                    platforms = platforms || '["discord"]'::jsonb
                WHERE id = $2 AND discord_id IS NULL
            """, discord_id, user_id)
            
            logger.info(f"✅ Discord привязан: user_id={user_id}, discord_id={discord_id}")
            return True
    
    async def link_website(self, user_id: int, website_email: str) -> bool:
        """Привязать Website к существующему пользователю"""
        async with self.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM unified_users WHERE website_email = $1",
                website_email
            )
            if existing:
                logger.warning(f"⚠️  Website email {website_email} уже привязан")
                return False
            
            await conn.execute("""
                UPDATE unified_users
                SET website_email = $1,
                    platforms = platforms || '["website"]'::jsonb
                WHERE id = $2 AND website_email IS NULL
            """, website_email, user_id)
            
            logger.info(f"✅ Website привязан: user_id={user_id}, email={website_email}")
            return True
    
    async def update_xp(self, user_id: int, delta_xp: int) -> Dict[str, Any]:
        """Обновить XP пользователя"""
        async with self.pool.acquire() as conn:
            # Получаем текущие данные
            user = await self.get_user_by_id(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            old_rank = user.rank_id
            new_xp = user.xp + delta_xp
            
            # Вычисляем новый ранг
            new_rank = calculate_rank_by_xp(new_xp)
            rank_up = new_rank.id > old_rank
            
            # Обновляем
            await conn.execute("""
                UPDATE unified_users
                SET xp = $1, rank_id = $2, last_active = CURRENT_TIMESTAMP
                WHERE id = $3
            """, new_xp, new_rank.id, user_id)
            
            # Если повышение ранга - выдаём награду
            if rank_up:
                reward_coins = new_rank.reward_coins
                await conn.execute("""
                    UPDATE unified_users
                    SET coins = coins + $1
                    WHERE id = $2
                """, reward_coins, user_id)
                
                logger.info(f"🎉 Повышение ранга: user_id={user_id}, {old_rank} → {new_rank.id}")
            
            return {
                'success': True,
                'xp': new_xp,
                'rank_up': rank_up,
                'old_rank': old_rank,
                'new_rank': new_rank.id,
                'reward_coins': new_rank.reward_coins if rank_up else 0
            }
    
    async def update_coins(self, user_id: int, delta_coins: int) -> int:
        """Обновить монеты пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                UPDATE unified_users
                SET coins = coins + $1, last_active = CURRENT_TIMESTAMP
                WHERE id = $2
                RETURNING coins
            """, delta_coins, user_id)
            
            return row['coins'] if row else 0
    
    async def get_leaderboard(self, limit: int = 10) -> List[UnifiedUser]:
        """Получить таблицу лидеров"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM unified_users
                ORDER BY xp DESC
                LIMIT $1
            """, limit)
            
            return [self._row_to_user(row) for row in rows]
    
    # ========================================================================
    # СОБЫТИЯ
    # ========================================================================
    
    async def create_event(
        self,
        user_id: int,
        event_type: str,
        source_platform: str,
        data: Dict[str, Any]
    ) -> str:
        """Создать событие синхронизации"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO cross_platform_events (user_id, event_type, source_platform, data)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, user_id, event_type, source_platform, data)
            
            event_id = str(row['id'])
            logger.info(f"📝 Событие создано: {event_type} от {source_platform}")
            return event_id
    
    async def get_pending_events(self, limit: int = 100) -> List[CrossPlatformEvent]:
        """Получить необработанные события"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM cross_platform_events
                WHERE processed = FALSE
                ORDER BY created_at ASC
                LIMIT $1
            """, limit)
            
            return [self._row_to_event(row) for row in rows]
    
    async def mark_event_processed(self, event_id: str):
        """Отметить событие как обработанное"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE cross_platform_events
                SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, event_id)
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    def _row_to_user(self, row) -> UnifiedUser:
        """Конвертировать строку БД в UnifiedUser"""
        if not row:
            return None
        
        return UnifiedUser(
            id=row['id'],
            telegram_id=row.get('telegram_id'),
            discord_id=row.get('discord_id'),
            website_email=row.get('website_email'),
            username=row['username'],
            display_name=row['display_name'],
            xp=row['xp'],
            coins=row['coins'],
            rank_id=row['rank_id'],
            games_played=row['games_played'],
            games_won=row['games_won'],
            total_voice_time=row['total_voice_time'],
            messages_sent=row['messages_sent'],
            achievements=row.get('achievements', []),
            current_season_xp=row['current_season_xp'],
            season_rank=row['season_rank'],
            daily_streak=row['daily_streak'],
            created_at=row['created_at'],
            last_active=row['last_active'],
            last_daily=row.get('last_daily'),
            platforms=row.get('platforms', []),
            primary_platform=row['primary_platform']
        )
    
    def _row_to_event(self, row) -> CrossPlatformEvent:
        """Конвертировать строку БД в CrossPlatformEvent"""
        return CrossPlatformEvent(
            id=str(row['id']),
            user_id=row['user_id'],
            event_type=row['event_type'],
            source_platform=row['source_platform'],
            data=row['data'],
            processed=row['processed'],
            processed_at=row.get('processed_at'),
            created_at=row['created_at']
        )


# Глобальный экземпляр
unified_db: Optional[UnifiedDatabase] = None


async def get_unified_db() -> UnifiedDatabase:
    """Получить экземпляр unified БД"""
    global unified_db
    
    if unified_db is None:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL не установлен")
        
        # Исправляем URL для asyncpg
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        unified_db = UnifiedDatabase(database_url)
        await unified_db.connect()
    
    return unified_db
