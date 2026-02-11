"""
Link Codes - Система одноразовых кодов для привязки аккаунтов
Генерирует короткие коды для быстрой привязки Discord к Telegram
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class LinkCodeManager:
    """Менеджер кодов привязки"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def connect(self):
        """Подключиться к БД"""
        import asyncpg
        
        # Исправляем URL для asyncpg
        db_url = self.database_url
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
        self.pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
        await self.init_table()
        logger.info("✅ LinkCodeManager подключен к БД")
    
    async def disconnect(self):
        """Отключиться от БД"""
        if self.pool:
            await self.pool.close()
    
    async def init_table(self):
        """Создать таблицу кодов привязки"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS link_codes (
                    code TEXT PRIMARY KEY,
                    telegram_id TEXT NOT NULL,
                    discord_id TEXT,
                    platform TEXT NOT NULL,
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP,
                    
                    INDEX idx_link_codes_telegram (telegram_id),
                    INDEX idx_link_codes_discord (discord_id),
                    INDEX idx_link_codes_expires (expires_at)
                );
            """)
    
    def generate_code(self, length: int = 6) -> str:
        """
        Генерировать случайный код
        
        Args:
            length: Длина кода (по умолчанию 6)
        
        Returns:
            Код из букв и цифр (например: ABC123)
        """
        # Используем только заглавные буквы и цифры (без похожих: 0/O, 1/I)
        chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    async def create_code(
        self,
        telegram_id: str,
        platform: str = 'telegram',
        expires_minutes: int = 10
    ) -> str:
        """
        Создать новый код привязки
        
        Args:
            telegram_id: ID пользователя Telegram
            platform: Платформа (telegram/discord)
            expires_minutes: Время жизни кода в минутах
        
        Returns:
            Сгенерированный код
        """
        # Генерируем уникальный код
        while True:
            code = self.generate_code()
            
            # Проверяем что код не существует
            async with self.pool.acquire() as conn:
                exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM link_codes WHERE code = $1)",
                    code
                )
                
                if not exists:
                    break
        
        # Вычисляем время истечения
        expires_at = datetime.now() + timedelta(minutes=expires_minutes)
        
        # Сохраняем код
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO link_codes (code, telegram_id, platform, expires_at)
                VALUES ($1, $2, $3, $4)
            """, code, telegram_id, platform, expires_at)
        
        logger.info(f"✅ Создан код привязки: {code} для {platform} {telegram_id}")
        return code
    
    async def verify_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Проверить код привязки
        
        Args:
            code: Код для проверки
        
        Returns:
            Данные кода или None если код недействителен
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM link_codes
                WHERE code = $1
                AND used = FALSE
                AND expires_at > CURRENT_TIMESTAMP
            """, code.upper())
            
            if not row:
                return None
            
            return dict(row)
    
    async def use_code(self, code: str, discord_id: str) -> bool:
        """
        Использовать код привязки
        
        Args:
            code: Код привязки
            discord_id: ID пользователя Discord
        
        Returns:
            True если код успешно использован
        """
        async with self.pool.acquire() as conn:
            # Проверяем и используем код
            result = await conn.execute("""
                UPDATE link_codes
                SET used = TRUE,
                    discord_id = $2,
                    used_at = CURRENT_TIMESTAMP
                WHERE code = $1
                AND used = FALSE
                AND expires_at > CURRENT_TIMESTAMP
            """, code.upper(), discord_id)
            
            # Проверяем что обновление прошло успешно
            if result == "UPDATE 1":
                logger.info(f"✅ Код {code} использован Discord {discord_id}")
                return True
            
            return False
    
    async def get_code_info(self, code: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о коде (включая использованные)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM link_codes WHERE code = $1",
                code.upper()
            )
            
            if not row:
                return None
            
            return dict(row)
    
    async def cleanup_expired(self):
        """Удалить истёкшие коды"""
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM link_codes
                WHERE expires_at < CURRENT_TIMESTAMP
                AND used = FALSE
            """)
            
            logger.info(f"🗑️ Удалено истёкших кодов: {result}")
    
    async def get_user_codes(self, telegram_id: str) -> list:
        """Получить все коды пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM link_codes
                WHERE telegram_id = $1
                ORDER BY created_at DESC
                LIMIT 10
            """, telegram_id)
            
            return [dict(row) for row in rows]


# Глобальный экземпляр
link_code_manager: Optional[LinkCodeManager] = None


async def get_link_code_manager() -> LinkCodeManager:
    """Получить экземпляр менеджера кодов"""
    global link_code_manager
    
    if link_code_manager is None:
        import os
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL не установлен")
        
        link_code_manager = LinkCodeManager(database_url)
        await link_code_manager.connect()
    
    return link_code_manager
