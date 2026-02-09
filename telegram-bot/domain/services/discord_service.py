"""
Discord Service - бизнес-логика Discord интеграции
"""
from typing import Optional, List
import logging

from domain.models.discord_link import DiscordLink, DiscordRoleGrant
from infrastructure.database.repositories.discord_repository import DiscordRepository
from infrastructure.external.discord_client import DiscordClient

logger = logging.getLogger(__name__)


class DiscordService:
    """Сервис для работы с Discord интеграцией"""
    
    def __init__(
        self,
        discord_repo: DiscordRepository,
        discord_client: Optional[DiscordClient] = None
    ):
        self.discord_repo = discord_repo
        self.discord_client = discord_client
    
    # ========================================================================
    # ПРИВЯЗКА АККАУНТОВ
    # ========================================================================
    
    async def create_link_request(
        self,
        telegram_user_id: int
    ) -> DiscordLink:
        """
        Создать запрос на привязку
        
        Returns:
            DiscordLink с кодом подтверждения
        """
        link = await self.discord_repo.create_link(telegram_user_id)
        
        logger.info(
            f"🔗 Создан запрос на привязку: telegram_user={telegram_user_id}, "
            f"code={link.verification_code}"
        )
        
        return link
    
    async def verify_link(
        self,
        verification_code: str,
        discord_user_id: int
    ) -> Optional[DiscordLink]:
        """
        Подтвердить привязку по коду
        
        Args:
            verification_code: 6-значный код
            discord_user_id: ID пользователя Discord
        
        Returns:
            DiscordLink если успешно, None если код неверный/истёк
        """
        link = await self.discord_repo.verify_link(
            verification_code,
            discord_user_id
        )
        
        if link:
            logger.info(
                f"✅ Привязка подтверждена: telegram_user={link.telegram_user_id}, "
                f"discord_user={discord_user_id}"
            )
            
            # Логируем
            await self.discord_repo.create_sync_log(
                telegram_user_id=link.telegram_user_id,
                discord_user_id=discord_user_id,
                action="link_created",
                success=True,
                details={"verification_code": verification_code}
            )
        else:
            logger.warning(
                f"❌ Неверный/истёкший код: {verification_code}"
            )
        
        return link
    
    async def get_active_link(
        self,
        telegram_user_id: int
    ) -> Optional[DiscordLink]:
        """Получить активную привязку пользователя"""
        return await self.discord_repo.get_active_link(telegram_user_id)
    
    async def revoke_link(self, telegram_user_id: int):
        """Отозвать привязку пользователя"""
        await self.discord_repo.revoke_link(telegram_user_id)
        
        logger.info(f"🔓 Привязка отозвана: telegram_user={telegram_user_id}")
    
    # ========================================================================
    # ВЫДАЧА РОЛЕЙ
    # ========================================================================
    
    async def grant_role(
        self,
        telegram_user_id: int,
        role_name: str,
        reason_type: str,
        reason_id: Optional[str] = None
    ) -> bool:
        """
        Выдать Discord роль пользователю
        
        Args:
            telegram_user_id: ID пользователя Telegram
            role_name: Название роли (например: "achievement_pro")
            reason_type: Тип причины (achievement, season_reward, rank)
            reason_id: ID причины (ID достижения, сезона, etc)
        
        Returns:
            True если роль выдана или запланирована
        """
        # Проверяем привязку
        link = await self.get_active_link(telegram_user_id)
        
        if not link or not link.discord_user_id:
            logger.warning(
                f"⚠️  Нет привязки Discord: telegram_user={telegram_user_id}"
            )
            return False
        
        # Создаём запись о выдаче роли
        grant = await self.discord_repo.create_role_grant(
            telegram_user_id=telegram_user_id,
            discord_user_id=link.discord_user_id,
            role_name=role_name,
            reason_type=reason_type,
            reason_id=reason_id
        )
        
        # Если есть Discord клиент - выдаём роль сразу
        if self.discord_client:
            success = await self._execute_role_grant(grant)
            return success
        else:
            logger.info(
                f"📌 Роль запланирована: telegram_user={telegram_user_id}, "
                f"role={role_name}"
            )
            return True
    
    async def _execute_role_grant(
        self,
        grant: DiscordRoleGrant
    ) -> bool:
        """Выполнить выдачу роли"""
        if not self.discord_client:
            return False
        
        # Находим ID роли по названию
        role_id = await self.discord_client.find_role_by_name(grant.role_name)
        
        if not role_id:
            error = f"Роль {grant.role_name} не найдена на сервере"
            await self.discord_repo.mark_role_failed(grant.id, error)
            
            await self.discord_repo.create_sync_log(
                telegram_user_id=grant.telegram_user_id,
                discord_user_id=grant.discord_user_id,
                action="role_grant_failed",
                success=False,
                error_message=error,
                details={"role_name": grant.role_name}
            )
            
            logger.error(f"❌ {error}")
            return False
        
        # Выдаём роль
        reason = f"{grant.reason_type}: {grant.reason_id}" if grant.reason_id else grant.reason_type
        
        success = await self.discord_client.add_role_to_member(
            user_id=grant.discord_user_id,
            role_id=role_id,
            reason=reason
        )
        
        if success:
            await self.discord_repo.mark_role_granted(grant.id, role_id)
            
            await self.discord_repo.create_sync_log(
                telegram_user_id=grant.telegram_user_id,
                discord_user_id=grant.discord_user_id,
                action="role_granted",
                success=True,
                details={
                    "role_name": grant.role_name,
                    "role_id": role_id,
                    "reason": reason
                }
            )
            
            logger.info(
                f"✅ Роль выдана: telegram_user={grant.telegram_user_id}, "
                f"role={grant.role_name}"
            )
        else:
            error = "Не удалось выдать роль через Discord API"
            await self.discord_repo.mark_role_failed(grant.id, error)
            
            await self.discord_repo.create_sync_log(
                telegram_user_id=grant.telegram_user_id,
                discord_user_id=grant.discord_user_id,
                action="role_grant_failed",
                success=False,
                error_message=error,
                details={"role_name": grant.role_name}
            )
        
        return success
    
    async def process_pending_role_grants(self) -> int:
        """
        Обработать невыданные роли
        
        Returns:
            Количество обработанных ролей
        """
        if not self.discord_client:
            return 0
        
        pending = await self.discord_repo.get_pending_role_grants()
        
        if not pending:
            return 0
        
        logger.info(f"📋 Обработка невыданных ролей: {len(pending)}")
        
        processed = 0
        for grant in pending:
            success = await self._execute_role_grant(grant)
            if success:
                processed += 1
        
        logger.info(f"✅ Обработано ролей: {processed}/{len(pending)}")
        
        return processed
    
    async def get_user_role_grants(
        self,
        telegram_user_id: int,
        granted_only: bool = False
    ) -> List[DiscordRoleGrant]:
        """Получить роли пользователя"""
        return await self.discord_repo.get_user_role_grants(
            telegram_user_id,
            granted_only=granted_only
        )
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    async def test_discord_connection(self) -> bool:
        """Проверить подключение к Discord"""
        if not self.discord_client:
            return False
        
        return await self.discord_client.test_connection()
    
    async def expire_old_codes(self):
        """Истечь старые коды подтверждения"""
        await self.discord_repo.expire_old_codes()
