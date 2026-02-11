"""
Achievement Repository - работа с достижениями в БД
"""
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from domain.models.achievement import Achievement, UserAchievement

logger = logging.getLogger(__name__)


class AchievementRepository:
    """Репозиторий для работы с достижениями"""
    
    def __init__(self, pool):
        self.pool = pool
    
    # ========================================================================
    # ДОСТИЖЕНИЯ
    # ========================================================================
    
    async def get_achievement(self, achievement_id: str) -> Optional[Achievement]:
        """Получить достижение по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM achievements
                WHERE id = $1
                """,
                achievement_id
            )
            
            if not row:
                return None
            
            return Achievement(**dict(row))
    
    async def get_all_achievements(
        self,
        category: Optional[str] = None,
        include_hidden: bool = False
    ) -> List[Achievement]:
        """
        Получить все достижения
        
        Args:
            category: Фильтр по категории
            include_hidden: Включить скрытые достижения
        """
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM achievements WHERE 1=1"
            params = []
            
            if category:
                params.append(category)
                query += f" AND category = ${len(params)}"
            
            if not include_hidden:
                query += " AND is_hidden = FALSE"
            
            query += " ORDER BY rarity DESC, requirement_value ASC"
            
            rows = await conn.fetch(query, *params)
            return [Achievement(**dict(row)) for row in rows]
    
    async def get_achievements_by_category(
        self,
        category: str
    ) -> List[Achievement]:
        """Получить достижения по категории"""
        return await self.get_all_achievements(category=category)
    
    # ========================================================================
    # ПРОГРЕСС ПОЛЬЗОВАТЕЛЯ
    # ========================================================================
    
    async def get_user_achievement(
        self,
        user_id: int,
        achievement_id: str
    ) -> Optional[UserAchievement]:
        """Получить прогресс пользователя по достижению"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM user_achievements
                WHERE user_id = $1 AND achievement_id = $2
                """,
                user_id, achievement_id
            )
            
            if not row:
                return None
            
            return UserAchievement(**dict(row))
    
    async def get_or_create_user_achievement(
        self,
        user_id: int,
        achievement_id: str,
        required_progress: int
    ) -> UserAchievement:
        """Получить или создать прогресс пользователя"""
        existing = await self.get_user_achievement(user_id, achievement_id)
        if existing:
            return existing
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_achievements (
                    user_id, achievement_id, current_progress,
                    required_progress, is_completed
                )
                VALUES ($1, $2, 0, $3, FALSE)
                RETURNING *
                """,
                user_id, achievement_id, required_progress
            )
            
            return UserAchievement(**dict(row))
    
    async def update_progress(
        self,
        user_id: int,
        achievement_id: str,
        progress: int
    ) -> UserAchievement:
        """
        Обновить прогресс пользователя
        
        Args:
            user_id: ID пользователя
            achievement_id: ID достижения
            progress: Новое значение прогресса
        """
        async with self.pool.acquire() as conn:
            # Получаем текущий прогресс
            current = await self.get_user_achievement(user_id, achievement_id)
            
            if not current:
                # Создаём если нет
                achievement = await self.get_achievement(achievement_id)
                if not achievement:
                    raise ValueError(f"Achievement {achievement_id} not found")
                
                current = await self.get_or_create_user_achievement(
                    user_id,
                    achievement_id,
                    achievement.requirement_value
                )
            
            # Проверяем не завершено ли уже
            if current.is_completed:
                return current
            
            # Обновляем прогресс
            is_completed = progress >= current.required_progress
            completed_at = datetime.now() if is_completed else None
            
            row = await conn.fetchrow(
                """
                UPDATE user_achievements
                SET current_progress = $1,
                    is_completed = $2,
                    completed_at = $3
                WHERE user_id = $4 AND achievement_id = $5
                RETURNING *
                """,
                progress, is_completed, completed_at,
                user_id, achievement_id
            )
            
            return UserAchievement(**dict(row))
    
    async def mark_rewards_claimed(
        self,
        user_id: int,
        achievement_id: str
    ):
        """Отметить что награды получены"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_achievements
                SET rewards_claimed = TRUE
                WHERE user_id = $1 AND achievement_id = $2
                """,
                user_id, achievement_id
            )
    
    # ========================================================================
    # СПИСКИ ДОСТИЖЕНИЙ ПОЛЬЗОВАТЕЛЯ
    # ========================================================================
    
    async def get_user_achievements(
        self,
        user_id: int,
        completed_only: bool = False
    ) -> List[Tuple[UserAchievement, Achievement]]:
        """
        Получить все достижения пользователя с прогрессом
        
        Returns:
            List of (UserAchievement, Achievement)
        """
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    ua.*,
                    a.id as ach_id,
                    a.name,
                    a.description,
                    a.category,
                    a.rarity,
                    a.requirement_type,
                    a.requirement_value,
                    a.reward_xp,
                    a.reward_coins,
                    a.reward_discord_role,
                    a.icon,
                    a.is_hidden,
                    a.created_at as ach_created_at
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.id
                WHERE ua.user_id = $1
            """
            
            if completed_only:
                query += " AND ua.is_completed = TRUE"
            
            query += " ORDER BY ua.is_completed DESC, a.rarity DESC, ua.current_progress DESC"
            
            rows = await conn.fetch(query, user_id)
            
            result = []
            for row in rows:
                # UserAchievement
                ua = UserAchievement(
                    id=row['id'],
                    user_id=row['user_id'],
                    achievement_id=row['achievement_id'],
                    current_progress=row['current_progress'],
                    required_progress=row['required_progress'],
                    is_completed=row['is_completed'],
                    completed_at=row['completed_at'],
                    rewards_claimed=row['rewards_claimed'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                
                # Achievement
                ach = Achievement(
                    id=row['ach_id'],
                    name=row['name'],
                    description=row['description'],
                    category=row['category'],
                    rarity=row['rarity'],
                    requirement_type=row['requirement_type'],
                    requirement_value=row['requirement_value'],
                    reward_xp=row['reward_xp'],
                    reward_coins=row['reward_coins'],
                    reward_discord_role=row['reward_discord_role'],
                    icon=row['icon'],
                    is_hidden=row['is_hidden'],
                    created_at=row['ach_created_at']
                )
                
                result.append((ua, ach))
            
            return result
    
    async def get_completed_achievements(
        self,
        user_id: int
    ) -> List[Tuple[UserAchievement, Achievement]]:
        """Получить завершённые достижения пользователя"""
        return await self.get_user_achievements(user_id, completed_only=True)
    
    async def get_unclaimed_achievements(
        self,
        user_id: int
    ) -> List[Tuple[UserAchievement, Achievement]]:
        """Получить завершённые но не полученные достижения"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT 
                    ua.*,
                    a.id as ach_id,
                    a.name,
                    a.description,
                    a.category,
                    a.rarity,
                    a.requirement_type,
                    a.requirement_value,
                    a.reward_xp,
                    a.reward_coins,
                    a.reward_discord_role,
                    a.icon,
                    a.is_hidden,
                    a.created_at as ach_created_at
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.id
                WHERE ua.user_id = $1
                    AND ua.is_completed = TRUE
                    AND ua.rewards_claimed = FALSE
                ORDER BY ua.completed_at ASC
            """
            
            rows = await conn.fetch(query, user_id)
            
            result = []
            for row in rows:
                ua = UserAchievement(
                    id=row['id'],
                    user_id=row['user_id'],
                    achievement_id=row['achievement_id'],
                    current_progress=row['current_progress'],
                    required_progress=row['required_progress'],
                    is_completed=row['is_completed'],
                    completed_at=row['completed_at'],
                    rewards_claimed=row['rewards_claimed'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                
                ach = Achievement(
                    id=row['ach_id'],
                    name=row['name'],
                    description=row['description'],
                    category=row['category'],
                    rarity=row['rarity'],
                    requirement_type=row['requirement_type'],
                    requirement_value=row['requirement_value'],
                    reward_xp=row['reward_xp'],
                    reward_coins=row['reward_coins'],
                    reward_discord_role=row['reward_discord_role'],
                    icon=row['icon'],
                    is_hidden=row['is_hidden'],
                    created_at=row['ach_created_at']
                )
                
                result.append((ua, ach))
            
            return result
    
    # ========================================================================
    # СТАТИСТИКА
    # ========================================================================
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Получить статистику достижений пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_completed = TRUE) as completed,
                    COUNT(*) FILTER (WHERE is_completed = FALSE) as in_progress
                FROM user_achievements
                WHERE user_id = $1
                """,
                user_id
            )
            
            return dict(row) if row else {
                'total': 0,
                'completed': 0,
                'in_progress': 0
            }
