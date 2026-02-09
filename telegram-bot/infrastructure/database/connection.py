"""
Database connection management
"""
import asyncpg
from typing import Optional
from core.config import Config


class DatabaseConnection:
    """Управление подключением к PostgreSQL"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Создать пул подключений"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                Config.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            print("✅ Подключено к PostgreSQL")
    
    async def disconnect(self):
        """Закрыть пул подключений"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("✅ Отключено от PostgreSQL")
    
    def get_pool(self) -> asyncpg.Pool:
        """Получить пул подключений"""
        if self.pool is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.pool


# Глобальный экземпляр
db_connection = DatabaseConnection()
