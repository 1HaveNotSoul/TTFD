"""
Ticket service - бизнес-логика тикетов
"""
from typing import Optional, List

from domain.models.ticket import (
    Ticket, TicketMessage, TicketStats,
    TicketStatus, TicketPriority, TicketCategory
)
from infrastructure.database.repositories.ticket_repository import TicketRepository
from core.exceptions import TicketError


class TicketService:
    """Сервис для работы с тикетами"""
    
    def __init__(self, ticket_repo: TicketRepository):
        self.ticket_repo = ticket_repo
    
    # ========================================================================
    # СОЗДАНИЕ И УПРАВЛЕНИЕ
    # ========================================================================
    
    async def create_ticket(
        self,
        user_id: int,
        category: str,
        priority: str,
        subject: str
    ) -> Ticket:
        """
        Создать тикет
        
        Args:
            user_id: ID пользователя
            category: Категория (general, technical, suggestion, complaint)
            priority: Приоритет (low, medium, high)
            subject: Текст тикета
        """
        # Валидация
        if len(subject) < 10:
            raise TicketError("Сообщение слишком короткое (минимум 10 символов)")
        
        if len(subject) > 1000:
            raise TicketError("Сообщение слишком длинное (максимум 1000 символов)")
        
        # Создаём тикет
        ticket = await self.ticket_repo.create(
            user_id=user_id,
            category=category,
            priority=priority,
            subject=subject
        )
        
        return ticket
    
    async def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """Получить тикет по ID"""
        return await self.ticket_repo.get_by_id(ticket_id)
    
    async def get_ticket_with_messages(self, ticket_id: int) -> Optional[Ticket]:
        """Получить тикет со всеми сообщениями"""
        return await self.ticket_repo.get_ticket_with_messages(ticket_id)
    
    async def get_user_tickets(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Ticket]:
        """Получить тикеты пользователя"""
        return await self.ticket_repo.get_user_tickets(user_id, status, limit)
    
    async def get_all_tickets(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[Ticket]:
        """Получить все тикеты (для админов)"""
        return await self.ticket_repo.get_all_tickets(status, priority, limit)
    
    async def close_ticket(self, ticket_id: int) -> Ticket:
        """Закрыть тикет"""
        return await self.ticket_repo.update_status(
            ticket_id,
            TicketStatus.CLOSED.value
        )
    
    async def reopen_ticket(self, ticket_id: int) -> Ticket:
        """Переоткрыть тикет"""
        return await self.ticket_repo.update_status(
            ticket_id,
            TicketStatus.OPEN.value
        )
    
    async def assign_ticket(
        self,
        ticket_id: int,
        admin_id: int
    ) -> Ticket:
        """Назначить тикет админу"""
        return await self.ticket_repo.assign_to(ticket_id, admin_id)
    
    # ========================================================================
    # СООБЩЕНИЯ
    # ========================================================================
    
    async def add_message(
        self,
        ticket_id: int,
        user_id: int,
        message: str,
        is_admin: bool = False
    ) -> TicketMessage:
        """
        Добавить сообщение в тикет
        
        Args:
            ticket_id: ID тикета
            user_id: ID пользователя
            message: Текст сообщения
            is_admin: Сообщение от админа
        """
        # Валидация
        if len(message) < 1:
            raise TicketError("Сообщение не может быть пустым")
        
        if len(message) > 1000:
            raise TicketError("Сообщение слишком длинное (максимум 1000 символов)")
        
        # Добавляем сообщение
        ticket_message = await self.ticket_repo.add_message(
            ticket_id=ticket_id,
            user_id=user_id,
            message=message,
            is_admin=is_admin
        )
        
        return ticket_message
    
    async def get_messages(self, ticket_id: int) -> List[TicketMessage]:
        """Получить все сообщения тикета"""
        return await self.ticket_repo.get_messages(ticket_id)
    
    # ========================================================================
    # СТАТИСТИКА
    # ========================================================================
    
    async def get_stats(self) -> TicketStats:
        """Получить статистику тикетов"""
        return await self.ticket_repo.get_stats()
    
    async def count_open_tickets(self) -> int:
        """Подсчитать открытые тикеты"""
        return await self.ticket_repo.count_by_status(TicketStatus.OPEN.value)
    
    async def count_high_priority_tickets(self) -> int:
        """Подсчитать тикеты с высоким приоритетом"""
        return await self.ticket_repo.count_by_priority(TicketPriority.HIGH.value)
    
    # ========================================================================
    # ПРОВЕРКИ
    # ========================================================================
    
    async def can_user_access_ticket(
        self,
        ticket_id: int,
        user_id: int,
        is_admin: bool = False
    ) -> bool:
        """Проверить может ли пользователь получить доступ к тикету"""
        ticket = await self.get_ticket(ticket_id)
        
        if not ticket:
            return False
        
        # Админы видят все тикеты
        if is_admin:
            return True
        
        # Пользователи видят только свои
        return ticket.user_id == user_id
