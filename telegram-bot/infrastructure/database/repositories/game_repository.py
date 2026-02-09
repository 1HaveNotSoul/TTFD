"""
Game repository - работа с играми в БД
"""
import asyncpg
from typing import Optional, List
from datetime import datetime
import json

from domain.models.game import GameSession, GameStats, GameType


class GameRepository:
    """Repository для работы с играми"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def create_session(
        self,
        user_id: int,
        game_type: str,
        bet_amount: int
    ) -> GameSession:
        """Создать игровую сессию"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO game_history (user_id, game_type, bet_amount, status)
                VALUES ($1, $2, $3, 'in_progress')
                RETURNING *
                """,
                user_id, game_type, bet_amount
            )
            return GameSession.from_db_row(row)
    
    async def complete_session(
        self,
        session_id: int,
        status: str,
        result: dict,
        reward_coins: int,
        reward_xp: int
    ) -> GameSession:
        """Завершить игровую сессию"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE game_history
                SET status = $1, result = $2, reward_coins = $3, reward_xp = $4,
                    completed_at = NOW()
                WHERE id = $5
                RETURNING *
                """,
                status, json.dumps(result), reward_coins, reward_xp, session_id
            )
            return GameSession.from_db_row(row)
    
    async def get_session(self, session_id: int) -> Optional[GameSession]:
        """Получить сессию по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM game_history WHERE id = $1",
                session_id
            )
            return GameSession.from_db_row(row)
    
    async def get_user_sessions(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[GameSession]:
        """Получить последние сессии пользователя"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM game_history
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                user_id, limit
            )
            return [GameSession.from_db_row(row) for row in rows]
    
    async def get_user_stats(self, user_id: int) -> GameStats:
        """Получить статистику игр пользователя"""
        async with self.pool.acquire() as conn:
            # Общая статистика
            total_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_games,
                    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as total_wins,
                    SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as total_losses,
                    SUM(CASE WHEN reward_coins > 0 THEN reward_coins ELSE 0 END) as total_coins_won,
                    SUM(CASE WHEN reward_coins < 0 THEN ABS(reward_coins) ELSE 0 END) as total_coins_lost,
                    SUM(reward_xp) as total_xp_earned
                FROM game_history
                WHERE user_id = $1 AND status IN ('won', 'lost')
                """,
                user_id
            )
            
            # Статистика по типам
            guess_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as games,
                    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins
                FROM game_history
                WHERE user_id = $1 AND game_type = 'guess_number' AND status IN ('won', 'lost')
                """,
                user_id
            )
            
            quiz_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as games,
                    SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins
                FROM game_history
                WHERE user_id = $1 AND game_type = 'quiz' AND status IN ('won', 'lost')
                """,
                user_id
            )
            
            spin_row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as count,
                    MAX(created_at) as last_spin
                FROM game_history
                WHERE user_id = $1 AND game_type = 'spin'
                """,
                user_id
            )
            
            return GameStats(
                user_id=user_id,
                total_games=total_row['total_games'] or 0,
                total_wins=total_row['total_wins'] or 0,
                total_losses=total_row['total_losses'] or 0,
                total_coins_won=total_row['total_coins_won'] or 0,
                total_coins_lost=total_row['total_coins_lost'] or 0,
                total_xp_earned=total_row['total_xp_earned'] or 0,
                guess_games=guess_row['games'] or 0,
                guess_wins=guess_row['wins'] or 0,
                quiz_games=quiz_row['games'] or 0,
                quiz_wins=quiz_row['wins'] or 0,
                spin_count=spin_row['count'] or 0,
                last_spin_at=spin_row['last_spin']
            )
    
    async def get_leaderboard(
        self,
        game_type: Optional[str] = None,
        limit: int = 10
    ) -> List[dict]:
        """Получить таблицу лидеров по играм"""
        async with self.pool.acquire() as conn:
            if game_type:
                rows = await conn.fetch(
                    """
                    SELECT 
                        u.telegram_id,
                        u.username,
                        u.first_name,
                        COUNT(*) as games_played,
                        SUM(CASE WHEN gh.status = 'won' THEN 1 ELSE 0 END) as games_won,
                        SUM(gh.reward_coins) as total_coins_won
                    FROM game_history gh
                    JOIN users u ON gh.user_id = u.id
                    WHERE gh.game_type = $1 AND gh.status IN ('won', 'lost')
                    GROUP BY u.id, u.telegram_id, u.username, u.first_name
                    ORDER BY games_won DESC, total_coins_won DESC
                    LIMIT $2
                    """,
                    game_type, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT 
                        u.telegram_id,
                        u.username,
                        u.first_name,
                        COUNT(*) as games_played,
                        SUM(CASE WHEN gh.status = 'won' THEN 1 ELSE 0 END) as games_won,
                        SUM(gh.reward_coins) as total_coins_won
                    FROM game_history gh
                    JOIN users u ON gh.user_id = u.id
                    WHERE gh.status IN ('won', 'lost')
                    GROUP BY u.id, u.telegram_id, u.username, u.first_name
                    ORDER BY games_won DESC, total_coins_won DESC
                    LIMIT $1
                    """,
                    limit
                )
            
            return [dict(row) for row in rows]
