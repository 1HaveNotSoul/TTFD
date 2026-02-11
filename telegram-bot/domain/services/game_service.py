"""
Game service - бизнес-логика игр
"""
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple

from domain.models.game import (
    GameSession, GameStats, GameType, GameStatus,
    QUIZ_QUESTIONS, SPIN_REWARDS
)
from domain.models.user import User
from infrastructure.database.repositories.game_repository import GameRepository
from infrastructure.database.repositories.user_repository import UserRepository
from core.exceptions import InsufficientFundsError, CooldownError


class GameService:
    """Сервис для работы с играми"""
    
    def __init__(
        self,
        game_repo: GameRepository,
        user_repo: UserRepository,
        season_service=None,  # Optional для обратной совместимости
        achievement_service=None  # Optional для обратной совместимости
    ):
        self.game_repo = game_repo
        self.user_repo = user_repo
        self.season_service = season_service
        self.achievement_service = achievement_service
    
    # ========================================================================
    # УГАДАЙ ЧИСЛО
    # ========================================================================
    
    async def start_guess_game(
        self,
        user: User,
        bet_amount: int
    ) -> Tuple[GameSession, int]:
        """
        Начать игру "Угадай число"
        
        Returns:
            (session, secret_number)
        """
        # Проверка баланса
        if user.coins < bet_amount:
            raise InsufficientFundsError(
                f"Недостаточно монет! У тебя: {user.coins}, нужно: {bet_amount}"
            )
        
        # Снимаем ставку
        await self.user_repo.update_coins(user.id, -bet_amount)
        
        # Создаём сессию
        session = await self.game_repo.create_session(
            user_id=user.id,
            game_type=GameType.GUESS_NUMBER.value,
            bet_amount=bet_amount
        )
        
        # Генерируем число от 1 до 10
        secret_number = random.randint(1, 10)
        
        return session, secret_number
    
    async def check_guess(
        self,
        session: GameSession,
        secret_number: int,
        guessed_number: int
    ) -> dict:
        """
        Проверить угаданное число
        
        Returns:
            dict с результатом
        """
        won = (secret_number == guessed_number)
        
        if won:
            # Выигрыш: ставка × 3
            reward_coins = session.bet_amount * 3
            reward_xp = 50
            status = GameStatus.WON.value
        else:
            # Проигрыш: утешительный XP
            reward_coins = 0
            reward_xp = 5
            status = GameStatus.LOST.value
        
        # Выдаём награды
        user = await self.user_repo.get_by_id(session.user_id)
        if reward_coins > 0:
            await self.user_repo.update_coins(user.id, reward_coins)
        await self.user_repo.update_xp(user.id, reward_xp)
        
        # Добавляем в сезонный прогресс
        if self.season_service:
            await self.season_service.add_season_xp(
                user_id=user.id,
                xp=reward_xp,
                coins=reward_coins,
                game_played=True,
                game_won=won
            )
        
        # Проверяем достижения
        if self.achievement_service:
            stats = await self.game_repo.get_user_stats(user.id)
            await self.achievement_service.check_game_achievements(
                user_id=user.id,
                games_played=stats.total_games,
                games_won=stats.total_wins
            )
            
            # Проверяем достижения за богатство
            await self.achievement_service.check_wealth_achievements(
                user_id=user.id,
                total_xp=user.xp + reward_xp,
                total_coins=user.coins + reward_coins
            )
        
        # Завершаем сессию
        result = {
            'secret_number': secret_number,
            'guessed_number': guessed_number,
            'won': won
        }
        
        await self.game_repo.complete_session(
            session_id=session.id,
            status=status,
            result=result,
            reward_coins=reward_coins,
            reward_xp=reward_xp
        )
        
        return {
            'won': won,
            'secret_number': secret_number,
            'reward_coins': reward_coins,
            'reward_xp': reward_xp
        }
    
    async def cancel_guess_game(self, session: GameSession):
        """Отменить игру - вернуть ставку"""
        # Возвращаем ставку
        await self.user_repo.update_coins(session.user_id, session.bet_amount)
        
        # Отмечаем как отменённую
        await self.game_repo.complete_session(
            session_id=session.id,
            status=GameStatus.CANCELLED.value,
            result={'cancelled': True},
            reward_coins=0,
            reward_xp=0
        )
    
    # ========================================================================
    # КВИЗ
    # ========================================================================
    
    def get_random_quiz(self) -> dict:
        """Получить случайный вопрос"""
        return random.choice(QUIZ_QUESTIONS)
    
    async def start_quiz_game(
        self,
        user: User,
        bet_amount: int
    ) -> Tuple[GameSession, dict]:
        """
        Начать квиз
        
        Returns:
            (session, quiz_question)
        """
        # Проверка баланса
        if user.coins < bet_amount:
            raise InsufficientFundsError(
                f"Недостаточно монет! У тебя: {user.coins}, нужно: {bet_amount}"
            )
        
        # Снимаем ставку
        await self.user_repo.update_coins(user.id, -bet_amount)
        
        # Создаём сессию
        session = await self.game_repo.create_session(
            user_id=user.id,
            game_type=GameType.QUIZ.value,
            bet_amount=bet_amount
        )
        
        # Получаем вопрос
        quiz = self.get_random_quiz()
        
        return session, quiz
    
    async def check_quiz_answer(
        self,
        session: GameSession,
        correct_index: int,
        user_answer_index: int
    ) -> dict:
        """
        Проверить ответ на квиз
        
        Returns:
            dict с результатом
        """
        correct = (correct_index == user_answer_index)
        
        if correct:
            # Правильный ответ: ставка × 2
            reward_coins = session.bet_amount * 2
            reward_xp = 30
            status = GameStatus.WON.value
        else:
            # Неправильный ответ: утешительный XP
            reward_coins = 0
            reward_xp = 5
            status = GameStatus.LOST.value
        
        # Выдаём награды
        user = await self.user_repo.get_by_id(session.user_id)
        if reward_coins > 0:
            await self.user_repo.update_coins(user.id, reward_coins)
        await self.user_repo.update_xp(user.id, reward_xp)
        
        # Добавляем в сезонный прогресс
        if self.season_service:
            await self.season_service.add_season_xp(
                user_id=user.id,
                xp=reward_xp,
                coins=reward_coins,
                game_played=True,
                game_won=correct
            )
        
        # Проверяем достижения
        if self.achievement_service:
            stats = await self.game_repo.get_user_stats(user.id)
            await self.achievement_service.check_game_achievements(
                user_id=user.id,
                games_played=stats.total_games,
                games_won=stats.total_wins
            )
            
            # Проверяем достижения за богатство
            await self.achievement_service.check_wealth_achievements(
                user_id=user.id,
                total_xp=user.xp + reward_xp,
                total_coins=user.coins + reward_coins
            )
        
        # Завершаем сессию
        result = {
            'correct_index': correct_index,
            'user_answer_index': user_answer_index,
            'correct': correct
        }
        
        await self.game_repo.complete_session(
            session_id=session.id,
            status=status,
            result=result,
            reward_coins=reward_coins,
            reward_xp=reward_xp
        )
        
        return {
            'correct': correct,
            'reward_coins': reward_coins,
            'reward_xp': reward_xp
        }
    
    async def cancel_quiz_game(self, session: GameSession):
        """Отменить квиз - вернуть ставку"""
        await self.user_repo.update_coins(session.user_id, session.bet_amount)
        
        await self.game_repo.complete_session(
            session_id=session.id,
            status=GameStatus.CANCELLED.value,
            result={'cancelled': True},
            reward_coins=0,
            reward_xp=0
        )
    
    # ========================================================================
    # ЕЖЕДНЕВНЫЙ СПИН
    # ========================================================================
    
    async def can_spin(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Проверить можно ли крутить спин
        
        Returns:
            (can_spin, time_left_str)
        """
        stats = await self.game_repo.get_user_stats(user_id)
        
        if not stats.last_spin_at:
            return True, None
        
        now = datetime.now()
        time_diff = (now - stats.last_spin_at).total_seconds()
        
        # 24 часа = 86400 секунд
        if time_diff >= 86400:
            return True, None
        
        time_left = 86400 - time_diff
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        
        return False, f"{hours}ч {minutes}м"
    
    async def spin_wheel(self, user: User) -> dict:
        """
        Крутить колесо фортуны
        
        Returns:
            dict с наградой
        """
        # Проверка кулдауна
        can_spin, time_left = await self.can_spin(user.id)
        if not can_spin:
            raise CooldownError(
                f"Ты уже крутил сегодня! Следующий спин через {time_left}"
            )
        
        # Выбираем награду с учётом весов
        rewards = []
        weights = []
        for reward in SPIN_REWARDS:
            rewards.append(reward)
            weights.append(reward['weight'])
        
        selected_reward = random.choices(rewards, weights=weights, k=1)[0]
        
        # Выдаём награду
        reward_coins = selected_reward['coins']
        reward_xp = selected_reward['xp']
        
        if reward_coins > 0:
            await self.user_repo.update_coins(user.id, reward_coins)
        
        if reward_xp > 0:
            await self.user_repo.update_xp(user.id, reward_xp)
        
        # Добавляем в сезонный прогресс
        if self.season_service:
            await self.season_service.add_season_xp(
                user_id=user.id,
                xp=reward_xp,
                coins=reward_coins,
                game_played=True,
                game_won=True  # Спин всегда выигрыш
            )
        
        # Проверяем достижения
        if self.achievement_service:
            stats = await self.game_repo.get_user_stats(user.id)
            await self.achievement_service.check_game_achievements(
                user_id=user.id,
                games_played=stats.total_games,
                games_won=stats.total_wins
            )
            
            # Проверяем достижения за богатство
            await self.achievement_service.check_wealth_achievements(
                user_id=user.id,
                total_xp=user.xp + reward_xp,
                total_coins=user.coins + reward_coins
            )
            
            # Проверяем специальное достижение за джекпот
            if selected_reward.get('name') == 'Джекпот':
                await self.achievement_service.check_special_achievement(
                    user_id=user.id,
                    achievement_id='lucky_spin'
                )
        
        # Создаём запись о спине
        session = await self.game_repo.create_session(
            user_id=user.id,
            game_type=GameType.SPIN.value,
            bet_amount=0
        )
        
        await self.game_repo.complete_session(
            session_id=session.id,
            status=GameStatus.WON.value,
            result={'reward': selected_reward},
            reward_coins=reward_coins,
            reward_xp=reward_xp
        )
        
        return {
            'reward': selected_reward,
            'coins': reward_coins,
            'xp': reward_xp
        }
    
    # ========================================================================
    # СТАТИСТИКА
    # ========================================================================
    
    async def get_user_stats(self, user_id: int) -> GameStats:
        """Получить статистику игр пользователя"""
        return await self.game_repo.get_user_stats(user_id)
    
    async def get_leaderboard(
        self,
        game_type: Optional[str] = None,
        limit: int = 10
    ) -> list:
        """Получить таблицу лидеров"""
        return await self.game_repo.get_leaderboard(game_type, limit)
