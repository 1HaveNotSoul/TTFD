"""
Discord Repository - работа с Discord привязками в БД
"""
from typing import Optional, List
from datetime import datetime, timedelta
import random
import string
import logging

from domain.models.discord_link import DiscordLink, DiscordRoleGrant, DiscordSyncLog

logger = logging.getLogger(__name__)


class DiscordRepository:
    """Репозиторий для работы с Discord интеграцией"""
    
    def __init__(self, pool):
        self.pool = pool
    
    # ========================================================================
    # ПРИВЯЗКИ
    # ========================================================================
    
    async def get_active_link(self, telegram_user_id: int) -> Optional[DiscordLink]:
        """Получить активную привязку пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM discord_links
                WHERE telegram_user_id = $1 AND status = 'active'
                """,
                telegram_user_id
            )
            
            if not row:
                return None
            
            return DiscordLink(**dict(row))
    
    async def get_link_by_code(self, verification_code: str) -> Optional[DiscordLink]:
        """Получить привязку по коду подтверждения"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM discord_links
                WHERE verification_code = $1 AND status = 'pending'
                """,
                verification_code
            )
            
            if not row:
                return None
            
            return DiscordLink(**dict(row))
    
    async def create_link(
        self,
        telegram_user_id: int,
        expires_in_minutes: int = 15
    ) -> DiscordLink:
        """
        Создать новую привязку с кодом подтверждения
        
        Args:
            telegram_user_id: ID пользователя Telegram
            expires_in_minutes: Время жизни кода в минутах
        """
        # Генерируем 6-значный код
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
        
        async with self.pool.acquire() as conn:
            # Отменяем старые pending привязки
            await conn.execute(
                """
                UPDATE discord_links
                SET status = 'expired'
                WHERE telegram_user_id = $1 AND status = 'pending'
                """,
                telegram_user_id
            )
            
            # Создаём новую
            row = await conn.fetchrow(
                """
                INSERT INTO discord_links (
                    telegram_user_id, verification_code, status, expires_at
                )
                VALUES ($1, $2, 'pending', $3)
                RETURNING *
                """,
                telegram_user_id, verification_code, expires_at
            )
            
            return DiscordLink(**dict(row))
    
    async def verify_link(
        self,
        verification_code: str,
        discord_user_id: int
    ) -> Optional[DiscordLink]:
        """
        Подтвердить привязку по коду
        
        Args:
            verification_code: Код подтверждения
            discord_user_id: ID пользователя Discord
        """
        async with self.pool.acquire() as conn:
            # Проверяем код
            link = await self.get_link_by_code(verification_code)
            
            if not link:
                return None
            
            # Проверяем не истёк ли
            if link.is_expired:
                await conn.execute(
                    """
                    UPDATE discord_links
                    SET status = 'expired'
                    WHERE id = $1
                    """,
                    link.id
                )
                return None
            
            # Отменяем старые активные привязки этого Discord пользователя
            await conn.execute(
                """
                UPDATE discord_links
                SET status = 'revoked'
                WHERE discord_user_id = $1 AND status = 'active'
                """,
                discord_user_id
            )
            
            # Активируем новую привязку
            row = await conn.fetchrow(
                """
                UPDATE discord_links
                SET discord_user_id = $1,
                    status = 'active',
                    verified_at = CURRENT_TIMESTAMP
                WHERE id = $2
                RETURNING *
                """,
                discord_user_id, link.id
            )
            
            return DiscordLink(**dict(row))
    
    async def revoke_link(self, telegram_user_id: int):
        """Отозвать привязку пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE discord_links
                SET status = 'revoked'
                WHERE telegram_user_id = $1 AND status = 'active'
                """,
                telegram_user_id
            )
    
    # ========================================================================
    # РОЛИ
    # ========================================================================
    
    async def create_role_grant(
        self,
        telegram_user_id: int,
        discord_user_id: int,
        role_name: str,
        reason_type: str,
        reason_id: Optional[str] = None
    ) -> DiscordRoleGrant:
        """Создать запись о выдаче роли"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO discord_role_grants (
                    telegram_user_id, discord_user_id, role_name,
                    reason_type, reason_id, is_granted
                )
                VALUES ($1, $2, $3, $4, $5, FALSE)
                ON CONFLICT (telegram_user_id, role_name, reason_type, reason_id)
                DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING *
                """,
                telegram_user_id, discord_user_id, role_name,
                reason_type, reason_id
            )
            
            return DiscordRoleGrant(**dict(row))
    
    async def mark_role_granted(
        self,
        grant_id: int,
        role_id: Optional[str] = None
    ):
        """Отметить что роль выдана"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE discord_role_grants
                SET is_granted = TRUE,
                    granted_at = CURRENT_TIMESTAMP,
                    role_id = $2,
                    error_message = NULL
                WHERE id = $1
                """,
                grant_id, role_id
            )
    
    async def mark_role_failed(
        self,
        grant_id: int,
        error_message: str
    ):
        """Отметить что выдача роли не удалась"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE discord_role_grants
                SET error_message = $2,
                    retry_count = retry_count + 1
                WHERE id = $1
                """,
                grant_id, error_message
            )
    
    async def get_pending_role_grants(
        self,
        telegram_user_id: Optional[int] = None,
        max_retries: int = 3
    ) -> List[DiscordRoleGrant]:
        """Получить невыданные роли"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT * FROM discord_role_grants
                WHERE is_granted = FALSE
                    AND retry_count < $1
            """
            params = [max_retries]
            
            if telegram_user_id:
                query += " AND telegram_user_id = $2"
                params.append(telegram_user_id)
            
            query += " ORDER BY created_at ASC"
            
            rows = await conn.fetch(query, *params)
            return [DiscordRoleGrant(**dict(row)) for row in rows]
    
    async def get_user_role_grants(
        self,
        telegram_user_id: int,
        granted_only: bool = False
    ) -> List[DiscordRoleGrant]:
        """Получить роли пользователя"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT * FROM discord_role_grants
                WHERE telegram_user_id = $1
            """
            
            if granted_only:
                query += " AND is_granted = TRUE"
            
            query += " ORDER BY created_at DESC"
            
            rows = await conn.fetch(query, telegram_user_id)
            return [DiscordRoleGrant(**dict(row)) for row in rows]
    
    # ========================================================================
    # ЛОГИ
    # ========================================================================
    
    async def create_sync_log(
        self,
        telegram_user_id: int,
        discord_user_id: int,
        action: str,
        success: bool,
        details: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> DiscordSyncLog:
        """Создать лог синхронизации"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO discord_sync_logs (
                    telegram_user_id, discord_user_id, action,
                    success, details, error_message
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                telegram_user_id, discord_user_id, action,
                success, details, error_message
            )
            
            return DiscordSyncLog(**dict(row))
    
    async def get_user_sync_logs(
        self,
        telegram_user_id: int,
        limit: int = 50
    ) -> List[DiscordSyncLog]:
        """Получить логи пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM discord_sync_logs
                WHERE telegram_user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                telegram_user_id, limit
            )
            
            return [DiscordSyncLog(**dict(row)) for row in rows]
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    async def expire_old_codes(self):
        """Истечь старые коды подтверждения"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE discord_links
                SET status = 'expired'
                WHERE status = 'pending'
                    AND expires_at < CURRENT_TIMESTAMP
                """
            )
            
            # Извлекаем количество обновлённых строк
            count = int(result.split()[-1]) if result else 0
            
            if count > 0:
                logger.info(f"Истекло кодов подтверждения: {count}")
