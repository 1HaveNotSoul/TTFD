"""
Centralized callback_data management
Стандартизация всех callback по доменам
"""
from enum import Enum
from typing import Optional


class CallbackDomain(Enum):
    """Домены callback_data"""
    MENU = "menu"
    PROFILE = "profile"
    GAME = "game"
    TICKET = "ticket"
    ADMIN = "admin"
    DISCORD = "discord"
    ECONOMY = "economy"


class CallbackBuilder:
    """
    Построитель callback_data с валидацией
    
    Формат: domain:action[:param1[:param2]]
    Примеры:
        menu:main
        profile:view:123
        game:guess:start
        game:guess:bet:50
        ticket:view:42
        admin:users:ban:123
    """
    
    SEPARATOR = ":"
    MAX_LENGTH = 64  # Telegram limit
    
    @classmethod
    def build(
        cls,
        domain: CallbackDomain,
        action: str,
        *params: str
    ) -> str:
        """
        Построить callback_data
        
        Args:
            domain: Домен (menu, profile, game, etc.)
            action: Действие (start, view, edit, etc.)
            *params: Дополнительные параметры
        
        Returns:
            Строка callback_data
        
        Raises:
            ValueError: Если callback слишком длинный
        """
        parts = [domain.value, action]
        parts.extend(str(p) for p in params)
        
        callback = cls.SEPARATOR.join(parts)
        
        if len(callback) > cls.MAX_LENGTH:
            raise ValueError(
                f"Callback слишком длинный: {len(callback)} > {cls.MAX_LENGTH}"
            )
        
        return callback
    
    @classmethod
    def parse(cls, callback_data: str) -> tuple[str, str, list[str]]:
        """
        Распарсить callback_data
        
        Args:
            callback_data: Строка callback
        
        Returns:
            (domain, action, params)
        
        Example:
            >>> parse("game:guess:bet:50")
            ("game", "guess", ["bet", "50"])
        """
        parts = callback_data.split(cls.SEPARATOR)
        
        if len(parts) < 2:
            raise ValueError(f"Неверный формат callback: {callback_data}")
        
        domain = parts[0]
        action = parts[1]
        params = parts[2:] if len(parts) > 2 else []
        
        return domain, action, params
    
    @classmethod
    def match(
        cls,
        callback_data: str,
        domain: CallbackDomain,
        action: Optional[str] = None
    ) -> bool:
        """
        Проверить соответствие callback домену и действию
        
        Args:
            callback_data: Строка callback
            domain: Ожидаемый домен
            action: Ожидаемое действие (опционально)
        
        Returns:
            True если соответствует
        """
        try:
            cb_domain, cb_action, _ = cls.parse(callback_data)
            
            if cb_domain != domain.value:
                return False
            
            if action and cb_action != action:
                return False
            
            return True
        
        except ValueError:
            return False


# ============================================================================
# MENU CALLBACKS
# ============================================================================

class MenuCallback:
    """Callback для главного меню"""
    
    @staticmethod
    def main() -> str:
        return CallbackBuilder.build(CallbackDomain.MENU, "main")
    
    @staticmethod
    def back() -> str:
        return CallbackBuilder.build(CallbackDomain.MENU, "back")


# ============================================================================
# PROFILE CALLBACKS
# ============================================================================

class ProfileCallback:
    """Callback для профиля"""
    
    @staticmethod
    def view(user_id: Optional[int] = None) -> str:
        if user_id:
            return CallbackBuilder.build(CallbackDomain.PROFILE, "view", str(user_id))
        return CallbackBuilder.build(CallbackDomain.PROFILE, "view")
    
    @staticmethod
    def stats() -> str:
        return CallbackBuilder.build(CallbackDomain.PROFILE, "stats")
    
    @staticmethod
    def settings() -> str:
        return CallbackBuilder.build(CallbackDomain.PROFILE, "settings")


# ============================================================================
# GAME CALLBACKS
# ============================================================================

class GameCallback:
    """Callback для игр"""
    
    @staticmethod
    def menu() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "menu")
    
    @staticmethod
    def stats() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "stats")
    
    # Guess game
    @staticmethod
    def guess_start() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "guess", "start")
    
    @staticmethod
    def guess_bet(amount: int) -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "guess", "bet", str(amount))
    
    @staticmethod
    def guess_number(number: int) -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "guess", "num", str(number))
    
    @staticmethod
    def guess_cancel() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "guess", "cancel")
    
    # Quiz game
    @staticmethod
    def quiz_start() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "quiz", "start")
    
    @staticmethod
    def quiz_bet(amount: int) -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "quiz", "bet", str(amount))
    
    @staticmethod
    def quiz_answer(index: int) -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "quiz", "ans", str(index))
    
    @staticmethod
    def quiz_cancel() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "quiz", "cancel")
    
    # Spin game
    @staticmethod
    def spin_start() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "spin", "start")
    
    @staticmethod
    def spin_do() -> str:
        return CallbackBuilder.build(CallbackDomain.GAME, "spin", "do")


# ============================================================================
# TICKET CALLBACKS
# ============================================================================

class TicketCallback:
    """Callback для тикетов"""
    
    @staticmethod
    def menu() -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "menu")
    
    @staticmethod
    def create_start() -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "create", "start")
    
    @staticmethod
    def category(category: str) -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "cat", category)
    
    @staticmethod
    def priority(priority: str) -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "pri", priority)
    
    @staticmethod
    def confirm() -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "confirm")
    
    @staticmethod
    def cancel() -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "cancel")
    
    @staticmethod
    def my_list() -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "my", "list")
    
    @staticmethod
    def view(ticket_id: int) -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "view", str(ticket_id))
    
    @staticmethod
    def close(ticket_id: int) -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "close", str(ticket_id))
    
    @staticmethod
    def reply(ticket_id: int) -> str:
        return CallbackBuilder.build(CallbackDomain.TICKET, "reply", str(ticket_id))


# ============================================================================
# ADMIN CALLBACKS
# ============================================================================

class AdminCallback:
    """Callback для админ-панели"""
    
    @staticmethod
    def panel() -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "panel")
    
    @staticmethod
    def stats() -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "stats")
    
    @staticmethod
    def users() -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "users")
    
    @staticmethod
    def tickets() -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "tickets")
    
    @staticmethod
    def database() -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "database")
    
    @staticmethod
    def db_table(table_name: str, page: int = 0) -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "db", table_name, str(page))
    
    @staticmethod
    def ticket_list(status: Optional[str] = None) -> str:
        if status:
            return CallbackBuilder.build(CallbackDomain.ADMIN, "ticket", "list", status)
        return CallbackBuilder.build(CallbackDomain.ADMIN, "ticket", "list", "all")
    
    @staticmethod
    def ticket_view(ticket_id: int) -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "ticket", "view", str(ticket_id))
    
    @staticmethod
    def ticket_assign(ticket_id: int) -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "ticket", "assign", str(ticket_id))
    
    @staticmethod
    def ticket_close(ticket_id: int) -> str:
        return CallbackBuilder.build(CallbackDomain.ADMIN, "ticket", "close", str(ticket_id))


# ============================================================================
# DISCORD CALLBACKS
# ============================================================================

class DiscordCallback:
    """Callback для Discord интеграции"""
    
    @staticmethod
    def menu() -> str:
        return CallbackBuilder.build(CallbackDomain.DISCORD, "menu")
    
    @staticmethod
    def link_start() -> str:
        return CallbackBuilder.build(CallbackDomain.DISCORD, "link", "start")
    
    @staticmethod
    def link_confirm() -> str:
        return CallbackBuilder.build(CallbackDomain.DISCORD, "link", "confirm")
    
    @staticmethod
    def unlink() -> str:
        return CallbackBuilder.build(CallbackDomain.DISCORD, "unlink")
    
    @staticmethod
    def rewards() -> str:
        return CallbackBuilder.build(CallbackDomain.DISCORD, "rewards")


# ============================================================================
# ECONOMY CALLBACKS
# ============================================================================

class EconomyCallback:
    """Callback для экономики"""
    
    @staticmethod
    def daily() -> str:
        return CallbackBuilder.build(CallbackDomain.ECONOMY, "daily")
    
    @staticmethod
    def shop() -> str:
        return CallbackBuilder.build(CallbackDomain.ECONOMY, "shop")
    
    @staticmethod
    def leaderboard() -> str:
        return CallbackBuilder.build(CallbackDomain.ECONOMY, "leaderboard")


# ============================================================================
# SEASON CALLBACKS
# ============================================================================

class SeasonCallback:
    """Callback для сезонов"""
    
    @staticmethod
    def info() -> str:
        return "season_info"
    
    @staticmethod
    def leaderboard() -> str:
        return "season_leaderboard"
    
    @staticmethod
    def rewards() -> str:
        return "season_rewards"
