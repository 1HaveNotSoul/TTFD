"""
Discord Client - взаимодействие с Discord API
"""
import aiohttp
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DiscordClient:
    """Клиент для работы с Discord API"""
    
    def __init__(self, bot_token: str, guild_id: str):
        """
        Args:
            bot_token: Токен Discord бота
            guild_id: ID сервера Discord
        """
        self.bot_token = bot_token
        self.guild_id = guild_id
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {bot_token}",
            "Content-Type": "application/json"
        }
    
    # ========================================================================
    # РОЛИ
    # ========================================================================
    
    async def add_role_to_member(
        self,
        user_id: int,
        role_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Выдать роль пользователю
        
        Args:
            user_id: ID пользователя Discord
            role_id: ID роли
            reason: Причина выдачи
        
        Returns:
            True если успешно
        """
        url = f"{self.base_url}/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}"
        
        headers = self.headers.copy()
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers) as response:
                    if response.status == 204:
                        logger.info(
                            f"✅ Роль выдана: user={user_id}, role={role_id}"
                        )
                        return True
                    else:
                        error = await response.text()
                        logger.error(
                            f"❌ Ошибка выдачи роли: status={response.status}, "
                            f"error={error}"
                        )
                        return False
        
        except Exception as e:
            logger.error(f"❌ Исключение при выдаче роли: {e}")
            return False
    
    async def remove_role_from_member(
        self,
        user_id: int,
        role_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Забрать роль у пользователя
        
        Args:
            user_id: ID пользователя Discord
            role_id: ID роли
            reason: Причина
        
        Returns:
            True если успешно
        """
        url = f"{self.base_url}/guilds/{self.guild_id}/members/{user_id}/roles/{role_id}"
        
        headers = self.headers.copy()
        if reason:
            headers["X-Audit-Log-Reason"] = reason
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    if response.status == 204:
                        logger.info(
                            f"✅ Роль забрана: user={user_id}, role={role_id}"
                        )
                        return True
                    else:
                        error = await response.text()
                        logger.error(
                            f"❌ Ошибка удаления роли: status={response.status}, "
                            f"error={error}"
                        )
                        return False
        
        except Exception as e:
            logger.error(f"❌ Исключение при удалении роли: {e}")
            return False
    
    async def get_guild_roles(self) -> List[dict]:
        """
        Получить все роли сервера
        
        Returns:
            Список ролей
        """
        url = f"{self.base_url}/guilds/{self.guild_id}/roles"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        roles = await response.json()
                        return roles
                    else:
                        error = await response.text()
                        logger.error(
                            f"❌ Ошибка получения ролей: status={response.status}, "
                            f"error={error}"
                        )
                        return []
        
        except Exception as e:
            logger.error(f"❌ Исключение при получении ролей: {e}")
            return []
    
    async def find_role_by_name(self, role_name: str) -> Optional[str]:
        """
        Найти ID роли по названию
        
        Args:
            role_name: Название роли
        
        Returns:
            ID роли или None
        """
        roles = await self.get_guild_roles()
        
        for role in roles:
            if role.get('name') == role_name:
                return role.get('id')
        
        return None
    
    # ========================================================================
    # ПОЛЬЗОВАТЕЛИ
    # ========================================================================
    
    async def get_guild_member(self, user_id: int) -> Optional[dict]:
        """
        Получить информацию о пользователе на сервере
        
        Args:
            user_id: ID пользователя Discord
        
        Returns:
            Информация о пользователе или None
        """
        url = f"{self.base_url}/guilds/{self.guild_id}/members/{user_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        member = await response.json()
                        return member
                    else:
                        return None
        
        except Exception as e:
            logger.error(f"❌ Исключение при получении пользователя: {e}")
            return None
    
    async def is_member_on_server(self, user_id: int) -> bool:
        """
        Проверить есть ли пользователь на сервере
        
        Args:
            user_id: ID пользователя Discord
        
        Returns:
            True если на сервере
        """
        member = await self.get_guild_member(user_id)
        return member is not None
    
    async def get_member_roles(self, user_id: int) -> List[str]:
        """
        Получить роли пользователя
        
        Args:
            user_id: ID пользователя Discord
        
        Returns:
            Список ID ролей
        """
        member = await self.get_guild_member(user_id)
        
        if not member:
            return []
        
        return member.get('roles', [])
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    async def test_connection(self) -> bool:
        """
        Проверить подключение к Discord API
        
        Returns:
            True если подключение работает
        """
        url = f"{self.base_url}/guilds/{self.guild_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        guild = await response.json()
                        logger.info(
                            f"✅ Подключение к Discord: {guild.get('name')}"
                        )
                        return True
                    else:
                        error = await response.text()
                        logger.error(
                            f"❌ Ошибка подключения к Discord: "
                            f"status={response.status}, error={error}"
                        )
                        return False
        
        except Exception as e:
            logger.error(f"❌ Исключение при подключении к Discord: {e}")
            return False
