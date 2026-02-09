"""
Permission and Role models
"""
from enum import Enum
from typing import List


class Permission(Enum):
    """Права доступа"""
    
    # Базовые права пользователя
    VIEW_PROFILE = "view_profile"
    EDIT_PROFILE = "edit_profile"
    USE_SHOP = "use_shop"
    PLAY_GAMES = "play_games"
    CREATE_TICKETS = "create_tickets"
    
    # VIP права
    VIP_SHOP_ACCESS = "vip_shop_access"
    VIP_DAILY_BONUS = "vip_daily_bonus"
    SKIP_COOLDOWNS = "skip_cooldowns"
    VIP_BADGE = "vip_badge"
    
    # Модератор
    VIEW_TICKETS = "view_tickets"
    ASSIGN_TICKETS = "assign_tickets"
    CLOSE_TICKETS = "close_tickets"
    MUTE_USERS = "mute_users"
    WARN_USERS = "warn_users"
    
    # Админ
    MANAGE_USERS = "manage_users"
    MANAGE_ECONOMY = "manage_economy"
    MANAGE_GAMES = "manage_games"
    VIEW_ANALYTICS = "view_analytics"
    BROADCAST = "broadcast"
    BAN_USERS = "ban_users"
    
    # Владелец
    MANAGE_ADMINS = "manage_admins"
    MANAGE_ROLES = "manage_roles"
    SYSTEM_CONFIG = "system_config"


class Role(Enum):
    """Роли пользователей"""
    USER = "user"
    VIP = "vip"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"


# Матрица прав: какие права есть у каждой роли
ROLE_PERMISSIONS: dict[Role, List[Permission]] = {
    Role.USER: [
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
        Permission.USE_SHOP,
        Permission.PLAY_GAMES,
        Permission.CREATE_TICKETS,
    ],
    
    Role.VIP: [
        # Все права USER +
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
        Permission.USE_SHOP,
        Permission.PLAY_GAMES,
        Permission.CREATE_TICKETS,
        # VIP права
        Permission.VIP_SHOP_ACCESS,
        Permission.VIP_DAILY_BONUS,
        Permission.SKIP_COOLDOWNS,
        Permission.VIP_BADGE,
    ],
    
    Role.MODERATOR: [
        # Все права VIP +
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
        Permission.USE_SHOP,
        Permission.PLAY_GAMES,
        Permission.CREATE_TICKETS,
        Permission.VIP_SHOP_ACCESS,
        Permission.VIP_DAILY_BONUS,
        Permission.SKIP_COOLDOWNS,
        Permission.VIP_BADGE,
        # Модератор права
        Permission.VIEW_TICKETS,
        Permission.ASSIGN_TICKETS,
        Permission.CLOSE_TICKETS,
        Permission.MUTE_USERS,
        Permission.WARN_USERS,
    ],
    
    Role.ADMIN: [
        # Все права MODERATOR +
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
        Permission.USE_SHOP,
        Permission.PLAY_GAMES,
        Permission.CREATE_TICKETS,
        Permission.VIP_SHOP_ACCESS,
        Permission.VIP_DAILY_BONUS,
        Permission.SKIP_COOLDOWNS,
        Permission.VIP_BADGE,
        Permission.VIEW_TICKETS,
        Permission.ASSIGN_TICKETS,
        Permission.CLOSE_TICKETS,
        Permission.MUTE_USERS,
        Permission.WARN_USERS,
        # Админ права
        Permission.MANAGE_USERS,
        Permission.MANAGE_ECONOMY,
        Permission.MANAGE_GAMES,
        Permission.VIEW_ANALYTICS,
        Permission.BROADCAST,
        Permission.BAN_USERS,
    ],
    
    Role.OWNER: [
        # Все права
        *[p for p in Permission]
    ]
}


def get_role_permissions(role: Role) -> List[Permission]:
    """Получить права роли"""
    return ROLE_PERMISSIONS.get(role, [])


def has_permission(role: Role, permission: Permission) -> bool:
    """Проверить есть ли право у роли"""
    return permission in get_role_permissions(role)


def get_role_from_string(role_str: str) -> Role:
    """Получить Role из строки"""
    try:
        return Role(role_str.lower())
    except ValueError:
        return Role.USER
