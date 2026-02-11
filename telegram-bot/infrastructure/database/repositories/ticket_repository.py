"""
Ticket repository - работа с тикетами в БД
"""
import asyncpg
from typing import Optional, List
from datetime import datetime

from domain.models.ticket import Ticket, TicketMessage, TicketStats


class TicketRepository:
    """Repository для работы с тикетами"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    # ========================================================================
    # ТИКЕТЫ
    # ========================================================================
    
    async def create(
        self,
        user_id: int,
        category: str,
        priority: str,
        subject: str
    ) -> Ticket:
        """Создать тикет"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO tickets (user_id, category, priority, subject)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                user_id, category, priority, subject
            )
            return Ticket.from_db_row(row)
    
    async def get_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Получить тикет по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM tickets WHERE id = $1",
                ticket_id
            )
            return Ticket.from_db_row(row)
    
    async def get_user_tickets(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Ticket]:
        """Получить тикеты пользователя"""
        async with self.pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tickets
                    WHERE user_id = $1 AND status = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    user_id, status, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM tickets
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    user_id, limit
                )
            
            return [Ticket.from_db_row(row) for row in rows]
    
    async def get_all_tickets(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[Ticket]:
        """Получить все тикеты (для админов)"""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM tickets WHERE 1=1"
            params = []
            param_count = 0
            
            if status:
                param_count += 1
                query += f" AND status = ${param_count}"
                params.append(status)
            
            if priority:
                param_count += 1
                query += f" AND priority = ${param_count}"
                params.append(priority)
            
            param_count += 1
            query += f" ORDER BY created_at DESC LIMIT ${param_count}"
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            return [Ticket.from_db_row(row) for row in rows]
    
    async def update_status(
        self,
        ticket_id: int,
        status: str
    ) -> Ticket:
        """Обновить статус тикета"""
        async with self.pool.acquire() as conn:
            # Если закрываем - ставим closed_at
            if status == 'closed':
                row = await conn.fetchrow(
                    """
                    UPDATE tickets
                    SET status = $1, closed_at = NOW()
                    WHERE id = $2
                    RETURNING *
                    """,
                    status, ticket_id
                )
            else:
                row = await conn.fetchrow(
                    """
                    UPDATE tickets
                    SET status = $1
                    WHERE id = $2
                    RETURNING *
                    """,
                    status, ticket_id
                )
            
            return Ticket.from_db_row(row)
    
    async def assign_to(
        self,
        ticket_id: int,
        admin_id: int
    ) -> Ticket:
        """Назначить тикет админу"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE tickets
                SET assigned_to = $1, status = 'in_progress'
                WHERE id = $2
                RETURNING *
                """,
                admin_id, ticket_id
            )
            return Ticket.from_db_row(row)
    
    async def count_by_status(self, status: str) -> int:
        """Подсчитать тикеты по статусу"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE status = $1",
                status
            )
    
    async def count_by_priority(self, priority: str) -> int:
        """Подсчитать тикеты по приоритету"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM tickets WHERE priority = $1",
                priority
            )
    
    async def get_stats(self) -> TicketStats:
        """Получить статистику тикетов"""
        async with self.pool.acquire() as conn:
            # Общая статистика
            total_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
                    SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high_priority,
                    SUM(CASE WHEN priority = 'medium' THEN 1 ELSE 0 END) as medium_priority,
                    SUM(CASE WHEN priority = 'low' THEN 1 ELSE 0 END) as low_priority
                FROM tickets
                """
            )
            
            return TicketStats(
                total=total_row['total'] or 0,
                open=total_row['open'] or 0,
                in_progress=total_row['in_progress'] or 0,
                closed=total_row['closed'] or 0,
                high_priority=total_row['high_priority'] or 0,
                medium_priority=total_row['medium_priority'] or 0,
                low_priority=total_row['low_priority'] or 0
            )
    
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
        """Добавить сообщение в тикет"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ticket_messages (ticket_id, user_id, message, is_admin)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """,
                ticket_id, user_id, message, is_admin
            )
            return TicketMessage.from_db_row(row)
    
    async def get_messages(self, ticket_id: int) -> List[TicketMessage]:
        """Получить все сообщения тикета"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT tm.*, u.first_name as user_name
                FROM ticket_messages tm
                JOIN users u ON tm.user_id = u.id
                WHERE tm.ticket_id = $1
                ORDER BY tm.created_at ASC
                """,
                ticket_id
            )
            
            messages = []
            for row in rows:
                msg = TicketMessage.from_db_row(row)
                msg.user_name = row['user_name']
                messages.append(msg)
            
            return messages
    
    async def get_ticket_with_messages(self, ticket_id: int) -> Optional[Ticket]:
        """Получить тикет со всеми сообщениями"""
        ticket = await self.get_by_id(ticket_id)
        if not ticket:
            return None
        
        ticket.messages = await self.get_messages(ticket_id)
        
        # Получаем имена пользователей
        async with self.pool.acquire() as conn:
            user_row = await conn.fetchrow(
                "SELECT first_name, username FROM users WHERE id = $1",
                ticket.user_id
            )
            if user_row:
                ticket.user_name = user_row['first_name']
            
            if ticket.assigned_to:
                admin_row = await conn.fetchrow(
                    "SELECT first_name FROM users WHERE id = $1",
                    ticket.assigned_to
                )
                if admin_row:
                    ticket.assigned_to_name = admin_row['first_name']
        
        return ticket
