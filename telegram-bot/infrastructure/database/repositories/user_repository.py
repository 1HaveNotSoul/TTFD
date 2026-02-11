"""
User repository - работа с пользователями в БД
"""
import asyncpg
from typing import Optional, List
from datetime import datetime

from domain.models.user import User


class UserRepository:
    """Repository для работы с пользователями"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            return User.from_db_row(row)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            return User.from_db_row(row)
    
    async def create(
        self,
        telegram_id: str,
        username: str,
        first_name: str
    ) -> User:
        """Создать нового пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (telegram_id, username, first_name)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                telegram_id, username, first_name
            )
            return User.from_db_row(row)
    
    async def update(self, user: User) -> User:
        """Обновить пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users 
                SET username = $1, first_name = $2, xp = $3, coins = $4,
                    rank_id = $5, role = $6, last_active = $7,
                    last_daily = $8, last_spin = $9, discord_id = $10,
                    is_banned = $11, ban_reason = $12
                WHERE id = $13
                RETURNING *
                """,
                user.username, user.first_name, user.xp, user.coins,
                user.rank_id, user.role, user.last_active,
                user.last_daily, user.last_spin, user.discord_id,
                user.is_banned, user.ban_reason, user.id
            )
            return User.from_db_row(row)
    
    async def update_xp(self, user_id: int, xp_delta: int) -> User:
        """Обновить XP (атомарно)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users 
                SET xp = xp + $1, last_active = NOW()
                WHERE id = $2
                RETURNING *
                """,
                xp_delta, user_id
            )
            return User.from_db_row(row)
    
    async def update_coins(self, user_id: int, coins_delta: int) -> User:
        """Обновить монеты (атомарно)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users 
                SET coins = coins + $1, last_active = NOW()
                WHERE id = $2
                RETURNING *
                """,
                coins_delta, user_id
            )
            return User.from_db_row(row)
    
    async def get_leaderboard(self, limit: int = 10) -> List[User]:
        """Получить топ пользователей по XP"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users ORDER BY xp DESC LIMIT $1",
                limit
            )
            return [User.from_db_row(row) for row in rows]
    
    async def get_all(self) -> List[User]:
        """Получить всех пользователей"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users")
            return [User.from_db_row(row) for row in rows]
    
    async def count(self) -> int:
        """Подсчитать количество пользователей"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users")
    
    async def update_last_active(self, user_id: int):
        """Обновить время последней активности"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_active = NOW() WHERE id = $1",
                user_id
            )
