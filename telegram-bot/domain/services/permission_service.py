"""
Permission service - проверка прав доступа
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from domain.models.user import User
from domain.models.permission import Permission, Role, has_permission, get_role_from_string
from core.exceptions import PermissionDeniedError
from core.config import Config


class PermissionService:
    """Сервис для работы с правами доступа"""
    
    @staticmethod
    def check_permission(user: User, permission: Permission) -> bool:
        """Проверить есть ли право у пользователя"""
        role = get_role_from_string(user.role)
        return has_permission(role, permission)
    
    @staticmethod
    def is_admin_by_id(telegram_id: str) -> bool:
        """Проверить является ли пользователь админом по Telegram ID"""
        return telegram_id in Config.TELEGRAM_ADMIN_IDS
    
    @staticmethod
    def require_admin_id():
        """
        Декоратор для проверки Telegram ID админа
        Проверяет что пользователь в списке TELEGRAM_ADMIN_IDS
        
        Использование:
        @PermissionService.require_admin_id()
        async def admin_command(self, update, context):
            ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                user_tg = update.effective_user
                telegram_id = str(user_tg.id)
                
                # Проверяем что ID в списке админов
                if not PermissionService.is_admin_by_id(telegram_id):
                    await update.message.reply_text(
                        "❌ У тебя нет доступа к этой команде\n"
                        "Только для администраторов платформы"
                    )
                    return
                
                # Выполняем функцию
                return await func(self, update, context, *args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def require_permission(permission: Permission):
        """
        Декоратор для проверки прав доступа
        
        Использование:
        @PermissionService.require_permission(Permission.MANAGE_USERS)
        async def ban_user(self, update, context):
            ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                # Получаем пользователя из контекста
                # (предполагается что user_service доступен через self)
                if not hasattr(self, 'user_service'):
                    raise RuntimeError("Handler должен иметь user_service для проверки прав")
                
                user_tg = update.effective_user
                user = await self.user_service.get_or_create_user(
                    str(user_tg.id),
                    user_tg.username or 'Unknown',
                    user_tg.first_name or ''
                )
                
                # Проверяем права
                if not PermissionService.check_permission(user, permission):
                    role = get_role_from_string(user.role)
                    await update.message.reply_text(
                        f"❌ У тебя нет прав для этого действия\n"
                        f"Требуется: {permission.value}\n"
                        f"Твоя роль: {role.value}"
                    )
                    return
                
                # Выполняем функцию
                return await func(self, update, context, *args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def require_role(required_role: Role):
        """
        Декоратор для проверки роли
        
        Использование:
        @PermissionService.require_role(Role.ADMIN)
        async def admin_panel(self, update, context):
            ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
                if not hasattr(self, 'user_service'):
                    raise RuntimeError("Handler должен иметь user_service для проверки прав")
                
                user_tg = update.effective_user
                user = await self.user_service.get_or_create_user(
                    str(user_tg.id),
                    user_tg.username or 'Unknown',
                    user_tg.first_name or ''
                )
                
                # Проверяем роль
                user_role = get_role_from_string(user.role)
                
                # Список ролей по приоритету
                role_hierarchy = [Role.USER, Role.VIP, Role.MODERATOR, Role.ADMIN, Role.OWNER]
                
                user_level = role_hierarchy.index(user_role)
                required_level = role_hierarchy.index(required_role)
                
                if user_level < required_level:
                    await update.message.reply_text(
                        f"❌ Недостаточно прав\n"
                        f"Требуется: {required_role.value}\n"
                        f"Твоя роль: {user_role.value}"
                    )
                    return
                
                return await func(self, update, context, *args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    async def get_user_permissions(user: User) -> list[Permission]:
        """Получить все права пользователя"""
        from domain.models.permission import get_role_permissions
        role = get_role_from_string(user.role)
        return get_role_permissions(role)
