"""
Season Repository - работа с сезонами в БД
"""
from typing import Optional, List
from datetime import datetime
import json

from domain.models.season import Season, SeasonProgress


class SeasonRepository:
    """Репозиторий для работы с сезонами"""
    
    def __init__(self, pool):
        self.pool = pool
    
    # ========================================================================
    # СЕЗОНЫ
    # ========================================================================
    
    async def get_active_season(self) -> Optional[Season]:
        """Получить активный сезон"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM seasons
                WHERE status = 'active'
                ORDER BY start_date DESC
                LIMIT 1
            """)
            
            if not row:
                return None
            
            return Season(
                id=row['id'],
                number=row['number'],
                name=row['name'],
                start_date=row['start_date'],
                end_date=row['end_date'],
                status=row['status'],
                rewards_config=row['rewards_config'],
                created_at=row['created_at']
            )
    
    async def get_season_by_id(self, season_id: int) -> Optional[Season]:
        """Получить сезон по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM seasons WHERE id = $1
            """, season_id)
            
            if not row:
                return None
            
            return Season(
                id=row['id'],
                number=row['number'],
                name=row['name'],
                start_date=row['start_date'],
                end_date=row['end_date'],
                status=row['status'],
                rewards_config=row['rewards_config'],
                created_at=row['created_at']
            )
    
    async def create_season(
        self,
        number: int,
        name: str,
        start_date: datetime,
        end_date: datetime,
        rewards_config: dict
    ) -> Season:
        """Создать новый сезон"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO seasons (number, name, start_date, end_date, status, rewards_config)
                VALUES ($1, $2, $3, $4, 'upcoming', $5)
                RETURNING *
            """, number, name, start_date, end_date, json.dumps(rewards_config))
            
            return Season(
                id=row['id'],
                number=row['number'],
                name=row['name'],
                start_date=row['start_date'],
                end_date=row['end_date'],
                status=row['status'],
                rewards_config=row['rewards_config'],
                created_at=row['created_at']
            )
    
    async def update_season_status(self, season_id: int, status: str):
        """Обновить статус сезона"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE seasons
                SET status = $1
                WHERE id = $2
            """, status, season_id)
    
    async def get_all_seasons(self) -> List[Season]:
        """Получить все сезоны"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM seasons
                ORDER BY number DESC
            """)
            
            return [
                Season(
                    id=row['id'],
                    number=row['number'],
                    name=row['name'],
                    start_date=row['start_date'],
                    end_date=row['end_date'],
                    status=row['status'],
                    rewards_config=row['rewards_config'],
                    created_at=row['created_at']
                )
                for row in rows
            ]
    
    # ========================================================================
    # ПРОГРЕСС ПОЛЬЗОВАТЕЛЕЙ
    # ========================================================================
    
    async def get_or_create_progress(
        self,
        user_id: int,
        season_id: int
    ) -> SeasonProgress:
        """Получить или создать прогресс пользователя в сезоне"""
        async with self.pool.acquire() as conn:
            # Пытаемся получить существующий
            row = await conn.fetchrow("""
                SELECT * FROM season_progress
                WHERE user_id = $1 AND season_id = $2
            """, user_id, season_id)
            
            if row:
                return self._row_to_progress(row)
            
            # Создаём новый
            row = await conn.fetchrow("""
                INSERT INTO season_progress (user_id, season_id)
                VALUES ($1, $2)
                RETURNING *
            """, user_id, season_id)
            
            return self._row_to_progress(row)
    
    async def update_progress(
        self,
        user_id: int,
        season_id: int,
        season_xp: Optional[int] = None,
        season_coins: Optional[int] = None,
        games_played: Optional[int] = None,
        games_won: Optional[int] = None,
        current_streak: Optional[int] = None,
        best_streak: Optional[int] = None,
        last_activity_date: Optional[datetime] = None
    ):
        """Обновить прогресс пользователя"""
        updates = []
        params = []
        param_count = 1
        
        if season_xp is not None:
            updates.append(f"season_xp = season_xp + ${param_count}")
            params.append(season_xp)
            param_count += 1
        
        if season_coins is not None:
            updates.append(f"season_coins = season_coins + ${param_count}")
            params.append(season_coins)
            param_count += 1
        
        if games_played is not None:
            updates.append(f"games_played = games_played + ${param_count}")
            params.append(games_played)
            param_count += 1
        
        if games_won is not None:
            updates.append(f"games_won = games_won + ${param_count}")
            params.append(games_won)
            param_count += 1
        
        if current_streak is not None:
            updates.append(f"current_streak = ${param_count}")
            params.append(current_streak)
            param_count += 1
        
        if best_streak is not None:
            updates.append(f"best_streak = GREATEST(best_streak, ${param_count})")
            params.append(best_streak)
            param_count += 1
        
        if last_activity_date is not None:
            updates.append(f"last_activity_date = ${param_count}")
            params.append(last_activity_date)
            param_count += 1
        
        if not updates:
            return
        
        params.extend([user_id, season_id])
        
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                UPDATE season_progress
                SET {', '.join(updates)}
                WHERE user_id = ${param_count} AND season_id = ${param_count + 1}
            """, *params)
    
    async def get_season_leaderboard(
        self,
        season_id: int,
        limit: int = 50
    ) -> List[tuple[SeasonProgress, str, str]]:
        """
        Получить рейтинг сезона
        
        Returns:
            List of (SeasonProgress, username, first_name)
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT sp.*, u.username, u.first_name
                FROM season_progress sp
                JOIN users u ON sp.user_id = u.id
                WHERE sp.season_id = $1
                ORDER BY sp.season_xp DESC
                LIMIT $2
            """, season_id, limit)
            
            return [
                (
                    self._row_to_progress(row),
                    row['username'],
                    row['first_name']
                )
                for row in rows
            ]
    
    async def update_ranks(self, season_id: int):
        """Обновить ранги всех пользователей в сезоне"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                WITH ranked AS (
                    SELECT 
                        id,
                        ROW_NUMBER() OVER (ORDER BY season_xp DESC) as new_rank
                    FROM season_progress
                    WHERE season_id = $1
                )
                UPDATE season_progress sp
                SET rank = ranked.new_rank
                FROM ranked
                WHERE sp.id = ranked.id
            """, season_id)
    
    async def mark_rewards_claimed(self, user_id: int, season_id: int):
        """Отметить что награды получены"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE season_progress
                SET rewards_claimed = TRUE
                WHERE user_id = $1 AND season_id = $2
            """, user_id, season_id)
    
    def _row_to_progress(self, row) -> SeasonProgress:
        """Конвертировать строку БД в SeasonProgress"""
        return SeasonProgress(
            id=row['id'],
            user_id=row['user_id'],
            season_id=row['season_id'],
            season_xp=row['season_xp'],
            season_coins=row['season_coins'],
            games_played=row['games_played'],
            games_won=row['games_won'],
            current_streak=row['current_streak'],
            best_streak=row['best_streak'],
            last_activity_date=row['last_activity_date'],
            rank=row['rank'],
            rewards_claimed=row['rewards_claimed'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
