"""
Season Service - бизнес-логика сезонов
"""
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
import logging

from domain.models.season import Season, SeasonProgress, SeasonReward, DEFAULT_SEASON_REWARDS
from infrastructure.database.repositories.season_repository import SeasonRepository
from domain.services.user_service import UserService

logger = logging.getLogger(__name__)


class SeasonService:
    """Сервис для работы с сезонами"""
    
    def __init__(
        self,
        season_repo: SeasonRepository,
        user_service: UserService,
        achievement_service=None,  # Optional для обратной совместимости
        discord_service=None  # Optional для обратной совместимости
    ):
        self.season_repo = season_repo
        self.user_service = user_service
        self.achievement_service = achievement_service
        self.discord_service = discord_service
    
    # ========================================================================
    # ПОЛУЧЕНИЕ СЕЗОНОВ
    # ========================================================================
    
    async def get_active_season(self) -> Optional[Season]:
        """Получить активный сезон"""
        return await self.season_repo.get_active_season()
    
    async def get_or_create_active_season(self) -> Season:
        """
        Получить активный сезон или создать новый если нет
        
        Автоматически создаёт новый сезон если:
        - Нет активного сезона
        - Текущий сезон закончился
        """
        season = await self.get_active_season()
        
        if season and season.is_active:
            return season
        
        # Создаём новый сезон
        return await self._create_next_season()
    
    async def _create_next_season(self) -> Season:
        """Создать следующий сезон"""
        all_seasons = await self.season_repo.get_all_seasons()
        next_number = len(all_seasons) + 1
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30)
        
        season = await self.season_repo.create_season(
            number=next_number,
            name=f"Сезон {next_number}",
            start_date=start_date,
            end_date=end_date,
            rewards_config=DEFAULT_SEASON_REWARDS
        )
        
        # Активируем сезон
        await self.season_repo.update_season_status(season.id, 'active')
        
        logger.info(f"🎉 Создан новый сезон #{next_number}")
        
        return season
    
    # ========================================================================
    # ПРОГРЕСС ПОЛЬЗОВАТЕЛЯ
    # ========================================================================
    
    async def get_user_progress(
        self,
        user_id: int,
        season_id: Optional[int] = None
    ) -> SeasonProgress:
        """
        Получить прогресс пользователя в сезоне
        
        Args:
            user_id: ID пользователя
            season_id: ID сезона (если None - активный сезон)
        """
        if season_id is None:
            season = await self.get_or_create_active_season()
            season_id = season.id
        
        return await self.season_repo.get_or_create_progress(user_id, season_id)
    
    async def add_season_xp(
        self,
        user_id: int,
        xp: int,
        coins: int = 0,
        game_played: bool = False,
        game_won: bool = False
    ):
        """
        Добавить XP/монеты в сезонный прогресс
        
        Вызывается после каждой игры/активности
        """
        season = await self.get_or_create_active_season()
        
        # Обновляем стрик
        await self._update_streak(user_id, season.id)
        
        # Обновляем прогресс
        await self.season_repo.update_progress(
            user_id=user_id,
            season_id=season.id,
            season_xp=xp,
            season_coins=coins,
            games_played=1 if game_played else 0,
            games_won=1 if game_won else 0,
            last_activity_date=datetime.now()
        )
        
        # Проверяем достижения за сезоны
        if self.achievement_service:
            progress = await self.season_repo.get_or_create_progress(user_id, season.id)
            await self.achievement_service.check_season_achievements(
                user_id=user_id,
                season_games=progress.games_played,
                season_rank=progress.rank
            )
        
        logger.debug(f"Добавлено в сезон: user={user_id}, xp={xp}, coins={coins}")
    
    async def _update_streak(self, user_id: int, season_id: int):
        """Обновить стрик пользователя"""
        progress = await self.season_repo.get_or_create_progress(user_id, season_id)
        
        now = datetime.now()
        
        # Если нет последней активности - начинаем стрик
        if not progress.last_activity_date:
            await self.season_repo.update_progress(
                user_id=user_id,
                season_id=season_id,
                current_streak=1,
                best_streak=1,
                last_activity_date=now
            )
            return
        
        # Проверяем разницу в днях
        days_diff = (now.date() - progress.last_activity_date.date()).days
        
        if days_diff == 0:
            # Сегодня уже была активность - ничего не делаем
            return
        elif days_diff == 1:
            # Вчера была активность - продолжаем стрик
            new_streak = progress.current_streak + 1
            await self.season_repo.update_progress(
                user_id=user_id,
                season_id=season_id,
                current_streak=new_streak,
                best_streak=new_streak,
                last_activity_date=now
            )
            
            # Проверяем достижения за стрики
            if self.achievement_service:
                await self.achievement_service.check_streak_achievements(
                    user_id=user_id,
                    current_streak=new_streak
                )
        else:
            # Пропущен день - сбрасываем стрик
            await self.season_repo.update_progress(
                user_id=user_id,
                season_id=season_id,
                current_streak=1,
                best_streak=progress.best_streak,  # Лучший стрик сохраняем
                last_activity_date=now
            )
    
    # ========================================================================
    # РЕЙТИНГ
    # ========================================================================
    
    async def get_season_leaderboard(
        self,
        season_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Tuple[SeasonProgress, str, str]]:
        """
        Получить рейтинг сезона
        
        Returns:
            List of (SeasonProgress, username, first_name)
        """
        if season_id is None:
            season = await self.get_or_create_active_season()
            season_id = season.id
        
        return await self.season_repo.get_season_leaderboard(season_id, limit)
    
    async def update_all_ranks(self):
        """
        Обновить ранги всех пользователей в активном сезоне
        
        Вызывается периодически (например, каждый час)
        """
        season = await self.get_active_season()
        if not season:
            return
        
        await self.season_repo.update_ranks(season.id)
        logger.info(f"Обновлены ранги для сезона #{season.number}")
    
    # ========================================================================
    # ЗАВЕРШЕНИЕ СЕЗОНА
    # ========================================================================
    
    async def check_season_end(self):
        """
        Проверить не закончился ли сезон
        
        Вызывается периодически (например, каждый час)
        """
        season = await self.get_active_season()
        
        if not season:
            return
        
        # Проверяем не истёк ли сезон
        if datetime.now() >= season.end_date:
            logger.info(f"🏁 Сезон #{season.number} завершён!")
            await self._end_season(season)
    
    async def _end_season(self, season: Season):
        """Завершить сезон и выдать награды"""
        # Обновляем финальные ранги
        await self.season_repo.update_ranks(season.id)
        
        # Получаем топ игроков
        leaderboard = await self.season_repo.get_season_leaderboard(
            season.id,
            limit=100
        )
        
        # Выдаём награды
        rewards_given = 0
        for progress, username, first_name in leaderboard:
            if progress.rank and not progress.rewards_claimed:
                reward = self._get_reward_for_rank(progress.rank, season.rewards_config)
                
                if reward:
                    await self._give_season_reward(
                        progress.user_id,
                        reward,
                        season.number
                    )
                    await self.season_repo.mark_rewards_claimed(
                        progress.user_id,
                        season.id
                    )
                    rewards_given += 1
        
        # Меняем статус сезона
        await self.season_repo.update_season_status(season.id, 'ended')
        
        logger.info(
            f"✅ Сезон #{season.number} завершён. "
            f"Награды выданы: {rewards_given} игрокам"
        )
        
        # Создаём новый сезон
        await self._create_next_season()
    
    def _get_reward_for_rank(
        self,
        rank: int,
        rewards_config: list
    ) -> Optional[dict]:
        """Получить награду для ранга"""
        for reward in rewards_config:
            if reward['rank_from'] <= rank <= reward['rank_to']:
                return reward
        return None
    
    async def _give_season_reward(
        self,
        user_id: int,
        reward: dict,
        season_number: int
    ):
        """Выдать награду за сезон"""
        # Добавляем XP и монеты
        user = await self.user_service.user_repo.get_by_id(user_id)
        if not user:
            return
        
        user.xp += reward['xp']
        user.coins += reward['coins']
        await self.user_service.user_repo.update(user)
        
        logger.info(
            f"🎁 Награда за сезон #{season_number}: "
            f"user={user_id}, xp={reward['xp']}, coins={reward['coins']}"
        )
        
        # Выдать Discord роль
        if reward.get('discord_role') and self.discord_service:
            await self.discord_service.grant_role(
                telegram_user_id=user_id,
                role_name=reward['discord_role'],
                reason_type="season_reward",
                reason_id=str(season_number)
            )
        
        # TODO: Сохранить титул в профиле
    
    # ========================================================================
    # СТАТИСТИКА
    # ========================================================================
    
    async def get_season_stats(self, season_id: Optional[int] = None) -> dict:
        """Получить статистику сезона"""
        if season_id is None:
            season = await self.get_or_create_active_season()
            season_id = season.id
        else:
            season = await self.season_repo.get_season_by_id(season_id)
        
        if not season:
            return {}
        
        leaderboard = await self.season_repo.get_season_leaderboard(season_id, limit=1000)
        
        total_players = len(leaderboard)
        total_xp = sum(p[0].season_xp for p in leaderboard)
        total_games = sum(p[0].games_played for p in leaderboard)
        
        return {
            'season': season,
            'total_players': total_players,
            'total_xp': total_xp,
            'total_games': total_games,
            'avg_xp_per_player': total_xp // total_players if total_players > 0 else 0,
            'days_left': season.days_left
        }
