"""
Custom exceptions
"""


class TTFDException(Exception):
    """Базовое исключение"""
    pass


class UserNotFoundError(TTFDException):
    """Пользователь не найден"""
    pass


class InsufficientFundsError(TTFDException):
    """Недостаточно средств"""
    pass


class PermissionDeniedError(TTFDException):
    """Нет прав доступа"""
    pass


class GameError(TTFDException):
    """Ошибка игры"""
    pass


class TicketError(TTFDException):
    """Ошибка тикета"""
    pass


class EconomyError(TTFDException):
    """Ошибка экономики"""
    pass


class CooldownError(TTFDException):
    """Кулдаун не истёк"""
    pass
