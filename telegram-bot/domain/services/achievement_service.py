"""
Achievement Service - бизнес-логика достижений
"""
from typing import Optional, List, Tuple
import logging

from domain.models.achievement import Achievement, UserAchievement
from infrastructure.database.repositories.achievement_repository import AchievementRepository
from domain.services.user_service import UserService

logger = logging.getLogger(__name__)


class AchievementService:
    """Сервис для работы с достижениями"""
    
    def __init__(
        self,
        achievement_repo: AchievementRepository,
        user_service: UserService,
        discord_service=None  # Optional для обратной совместимости
    ):
        self.achievement_repo = achievement_repo
        self.user_service = user_service
        self.discord_service = discord_service
    
    # ========================================================================
    # ПОЛУЧЕНИЕ ДОСТИЖЕНИЙ
    # ========================================================================
    
    async def get_all_achievements(
        self,
        category: Optional[str] = None,
        include_hidden: bool = False
    ) -> List[Achievement]:
        """Получить все достижения"""
        return await self.achievement_repo.get_all_achievements(
            category=category,
            include_hidden=include_hidden
        )
    
    async def get_user_achievements(
        self,
        user_id: int,
        completed_only: bool = False
    ) -> List[Tuple[UserAchievement, Achievement]]:
        """Получить достижения пользователя с прогрессом"""
        return await self.achievement_repo.get_user_achievements(
            user_id,
            completed_only=completed_only
        )
    
    async def get_completed_achievements(
        self,
        user_id: int
    ) -> List[Tuple[UserAchievement, Achievement]]:
        """Получить завершённые достижения"""
        return await self.achievement_repo.get_completed_achievements(user_id)
    
    # ========================================================================
    # ПРОВЕРКА ДОСТИЖЕНИЙ
    # ========================================================================
    
    async def check_achievements(
        self,
        user_id: int,
        trigger_type: str,
        current_value: int
    ) -> List[Achievement]:
        """
        Проверить достижения пользователя
        
        Args:
            user_id: ID пользователя
            trigger_type: Тип триггера (games_won, streak_days, etc.)
            current_value: Текущее значение
        
        Returns:
            Список новых завершённых достижений
        """
        # Получаем все достижения этого типа
        all_achievements = await self.achievement_repo.get_all_achievements(
            include_hidden=True
        )
        
        relevant_achievements = [
            ach for ach in all_achievements
            if ach.requirement_type == trigger_type
        ]
        
        newly_completed = []
        
        for achievement in relevant_achievements:
            # Получаем или создаём прогресс
            progress = await self.achievement_repo.get_or_create_user_achievement(
                user_id,
                achievement.id,
                achievement.requirement_value
            )
            
            # Если уже завершено - пропускаем
            if progress.is_completed:
                continue
            
            # Обновляем прогресс
            updated_progress = await self.achievement_repo.update_progress(
                user_id,
                achievement.id,
                current_value
            )
            
            # Если только что завершилось - добавляем в список
            if updated_progress.is_completed and not progress.is_completed:
                newly_completed.append(achievement)
                logger.info(
                    f"🏆 Достижение получено: user={user_id}, "
                    f"achievement={achievement.id} ({achievement.name})"
                )
        
        # Выдаём награды за новые достижения
        for achievement in newly_completed:
            await self._give_achievement_reward(user_id, achievement)
        
        return newly_completed
    
    async def _give_achievement_reward(
        self,
        user_id: int,
        achievement: Achievement
    ):
        """Выдать награду за достижение"""
        user = await self.user_service.user_repo.get_by_id(user_id)
        if not user:
            return
        
        # Добавляем XP и монеты
        if achievement.reward_xp > 0:
            await self.user_service.user_repo.update_xp(
                user_id,
                achievement.reward_xp
            )
        
        if achievement.reward_coins > 0:
            await self.user_service.user_repo.update_coins(
                user_id,
                achievement.reward_coins
            )
        
        # Отмечаем что награды получены
        await self.achievement_repo.mark_rewards_claimed(
            user_id,
            achievement.id
        )
        
        logger.info(
            f"🎁 Награда за достижение: user={user_id}, "
            f"achievement={achievement.id}, "
            f"xp={achievement.reward_xp}, coins={achievement.reward_coins}"
        )
        
        # Выдать Discord роль
        if achievement.reward_discord_role and self.discord_service:
            await self.discord_service.grant_role(
                telegram_user_id=user_id,
                role_name=achievement.reward_discord_role,
                reason_type="achievement",
                reason_id=achievement.id
            )
    
    # ========================================================================
    # СПЕЦИАЛЬНЫЕ ПРОВЕРКИ
    # ========================================================================
    
    async def check_game_achievements(
        self,
        user_id: int,
        games_played: int,
        games_won: int
    ):
        """
        Проверить достижения связанные с играми
        
        Вызывается после каждой игры
        """
        # Проверяем достижения за победы
        await self.check_achievements(user_id, "games_won", games_won)
        
        # Проверяем достижения за активность
        await self.check_achievements(user_id, "games_played", games_played)
    
    async def check_streak_achievements(
        self,
        user_id: int,
        current_streak: int
    ):
        """
        Проверить достижения за стрики
        
        Вызывается при обновлении стрика
        """
        await self.check_achievements(user_id, "streak_days", current_streak)
    
    async def check_wealth_achievements(
        self,
        user_id: int,
        total_xp: int,
        total_coins: int
    ):
        """
        Проверить достижения за богатство
        
        Вызывается при изменении XP/монет
        """
        await self.check_achievements(user_id, "total_xp", total_xp)
        await self.check_achievements(user_id, "total_coins", total_coins)
    
    async def check_ticket_achievements(
        self,
        user_id: int,
        tickets_created: int,
        tickets_resolved: int
    ):
        """
        Проверить достижения за тикеты
        
        Вызывается при создании/закрытии тикета
        """
        await self.check_achievements(user_id, "tickets_created", tickets_created)
        await self.check_achievements(user_id, "tickets_resolved", tickets_resolved)
    
    async def check_season_achievements(
        self,
        user_id: int,
        season_games: int,
        season_rank: Optional[int] = None
    ):
        """
        Проверить достижения за сезоны
        
        Вызывается при обновлении сезонного прогресса
        """
        await self.check_achievements(user_id, "season_games", season_games)
        
        if season_rank:
            # Для рангов проверяем "меньше или равно"
            # Например: rank=5 должен дать достижения за топ-50, топ-10
            all_achievements = await self.achievement_repo.get_all_achievements(
                include_hidden=True
            )
            
            rank_achievements = [
                ach for ach in all_achievements
                if ach.requirement_type == "season_rank"
            ]
            
            for achievement in rank_achievements:
                # Если ранг меньше или равен требуемому - засчитываем
                if season_rank <= achievement.requirement_value:
                    progress = await self.achievement_repo.get_or_create_user_achievement(
                        user_id,
                        achievement.id,
                        achievement.requirement_value
                    )
                    
                    if not progress.is_completed:
                        await self.achievement_repo.update_progress(
                            user_id,
                            achievement.id,
                            achievement.requirement_value  # Сразу завершаем
                        )
                        
                        await self._give_achievement_reward(user_id, achievement)
                        
                        logger.info(
                            f"🏆 Сезонное достижение: user={user_id}, "
                            f"achievement={achievement.id}, rank={season_rank}"
                        )
    
    async def check_special_achievement(
        self,
        user_id: int,
        achievement_id: str
    ):
        """
        Проверить специальное достижение
        
        Используется для редких/скрытых достижений
        """
        achievement = await self.achievement_repo.get_achievement(achievement_id)
        if not achievement:
            return
        
        progress = await self.achievement_repo.get_or_create_user_achievement(
            user_id,
            achievement_id,
            achievement.requirement_value
        )
        
        if not progress.is_completed:
            await self.achievement_repo.update_progress(
                user_id,
                achievement_id,
                achievement.requirement_value
            )
            
            await self._give_achievement_reward(user_id, achievement)
            
            logger.info(
                f"🌟 Специальное достижение: user={user_id}, "
                f"achievement={achievement_id}"
            )
    
    # ========================================================================
    # СТАТИСТИКА
    # ========================================================================
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Получить статистику достижений пользователя"""
        stats = await self.achievement_repo.get_user_stats(user_id)
        
        # Добавляем процент завершения
        if stats['total'] > 0:
            stats['completion_percent'] = (
                stats['completed'] / stats['total']
            ) * 100
        else:
            stats['completion_percent'] = 0.0
        
        return stats
    
    async def get_unclaimed_achievements(
        self,
        user_id: int
    ) -> List[Tuple[UserAchievement, Achievement]]:
        """Получить незабранные награды"""
        return await self.achievement_repo.get_unclaimed_achievements(user_id)
    
    # ========================================================================
    # ФОРМАТИРОВАНИЕ
    # ========================================================================
    
    @staticmethod
    def format_rarity(rarity: str) -> str:
        """Форматировать редкость"""
        rarity_map = {
            'common': '⚪ Обычное',
            'rare': '🔵 Редкое',
            'epic': '🟣 Эпическое',
            'legendary': '🟡 Легендарное'
        }
        return rarity_map.get(rarity, rarity)
    
    @staticmethod
    def format_category(category: str) -> str:
        """Форматировать категорию"""
        category_map = {
            'games': '🎮 Игры',
            'activity': '⚡ Активность',
            'streak': '🔥 Стрики',
            'tickets': '🎫 Тикеты',
            'season': '🏆 Сезоны',
            'special': '🌟 Специальные'
        }
        return category_map.get(category, category)
