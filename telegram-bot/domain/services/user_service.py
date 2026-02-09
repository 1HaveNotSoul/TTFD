"""
User service - бизнес-логика работы с пользователями
"""
from typing import Optional, List
from datetime import datetime, timedelta

from domain.models.user import User, Rank, get_rank_by_id, calculate_rank_by_xp, RANKS
from infrastructure.database.repositories.user_repository import UserRepository
from core.exceptions import UserNotFoundError, CooldownError
from core.config import Config


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, user_repo: UserRepository, cache=None):
        self.user_repo = user_repo
        self.cache = cache
    
    async def _get_from_cache(self, key: str):
        """Получить из кэша"""
        if self.cache:
            return await self.cache.get(key)
        return None
    
    async def _set_to_cache(self, key: str, value, ttl: int):
        """Сохранить в кэш"""
        if self.cache:
            await self.cache.set(key, value, ttl)
    
    async def _invalidate_cache(self, telegram_id: str):
        """Инвалидировать кэш пользователя"""
        if self.cache:
            await self.cache.delete(f"user:profile:{telegram_id}")
            await self.cache.invalidate_pattern("leaderboard:*")
    
    async def get_or_create_user(
        self,
        telegram_id: str,
        username: str,
        first_name: str
    ) -> User:
        """Получить или создать пользователя"""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            user = await self.user_repo.create(telegram_id, username, first_name)
            print(f"✨ Новый пользователь: {username} ({telegram_id})")
        else:
            # Обновляем last_active
            await self.user_repo.update_last_active(user.id)
        
        return user
    
    async def get_user(self, telegram_id: str) -> User:
        """Получить пользователя"""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise UserNotFoundError(f"Пользователь {telegram_id} не найден")
        return user
    
    async def add_xp(self, telegram_id: str, amount: int) -> dict:
        """Добавить XP пользователю"""
        user = await self.get_user(telegram_id)
        old_rank_id = user.rank_id
        
        # Обновляем XP
        user = await self.user_repo.update_xp(user.id, amount)
        
        # Инвалидируем кэш
        await self._invalidate_cache(telegram_id)
        
        # Проверяем повышение ранга
        new_rank = calculate_rank_by_xp(user.xp)
        
        if new_rank.id > old_rank_id:
            # Повышение ранга!
            user.rank_id = new_rank.id
            user.coins += new_rank.reward_coins
            user = await self.user_repo.update(user)
            
            return {
                'xp': user.xp,
                'rank_up': True,
                'old_rank': get_rank_by_id(old_rank_id),
                'new_rank': new_rank,
                'reward_coins': new_rank.reward_coins
            }
        
        return {
            'xp': user.xp,
            'rank_up': False,
            'old_rank': get_rank_by_id(old_rank_id),
            'new_rank': get_rank_by_id(user.rank_id)
        }
    
    async def add_coins(self, telegram_id: str, amount: int) -> int:
        """Добавить монеты пользователю"""
        user = await self.get_user(telegram_id)
        user = await self.user_repo.update_coins(user.id, amount)
        return user.coins
    
    async def remove_coins(self, telegram_id: str, amount: int) -> bool:
        """Убрать монеты у пользователя"""
        user = await self.get_user(telegram_id)
        
        if user.coins < amount:
            return False
        
        await self.user_repo.update_coins(user.id, -amount)
        return True
    
    async def can_claim_daily(self, telegram_id: str) -> bool:
        """Проверить можно ли получить ежедневную награду"""
        user = await self.get_user(telegram_id)
        
        if not user.last_daily:
            return True
        
        time_diff = (datetime.now() - user.last_daily).total_seconds()
        return time_diff >= (Config.DAILY_COOLDOWN_HOURS * 3600)
    
    async def claim_daily(self, telegram_id: str) -> dict:
        """Получить ежедневную награду"""
        user = await self.get_user(telegram_id)
        
        # Проверяем кулдаун
        if user.last_daily:
            time_diff = (datetime.now() - user.last_daily).total_seconds()
            cooldown_seconds = Config.DAILY_COOLDOWN_HOURS * 3600
            
            if time_diff < cooldown_seconds:
                time_left = int(cooldown_seconds - time_diff)
                hours = time_left // 3600
                minutes = (time_left % 3600) // 60
                raise CooldownError(
                    f'Ты уже получил награду! Следующая через {hours}ч {minutes}м',
                    time_left
                )
        
        # Начисляем награды
        xp_result = await self.add_xp(telegram_id, Config.DAILY_REWARD_XP)
        coins = await self.add_coins(telegram_id, Config.DAILY_REWARD_COINS)
        
        # Обновляем last_daily
        user.last_daily = datetime.now()
        await self.user_repo.update(user)
        
        return {
            'success': True,
            'xp': Config.DAILY_REWARD_XP,
            'coins': Config.DAILY_REWARD_COINS,
            'rank_up': xp_result['rank_up'],
            'new_rank': xp_result['new_rank'] if xp_result['rank_up'] else None
        }
    
    async def get_leaderboard(self, limit: int = 10) -> List[User]:
        """Получить таблицу лидеров (с кэшированием)"""
        cache_key = f"leaderboard:{limit}"
        
        # Проверяем кэш
        cached = await self._get_from_cache(cache_key)
        if cached:
            return [User(**u) for u in cached]
        
        # Загружаем из БД
        users = await self.user_repo.get_leaderboard(limit)
        
        # Сохраняем в кэш на 1 минуту
        await self._set_to_cache(
            cache_key,
            [u.to_dict() for u in users],
            Config.CACHE_TTL_LEADERBOARD
        )
        
        return users
    
    async def get_user_rank(self, telegram_id: str) -> Rank:
        """Получить ранг пользователя"""
        user = await self.get_user(telegram_id)
        return get_rank_by_id(user.rank_id)
    
    async def get_next_rank(self, telegram_id: str) -> Optional[Rank]:
        """Получить следующий ранг"""
        user = await self.get_user(telegram_id)
        
        if user.rank_id >= len(RANKS):
            return None  # Максимальный ранг
        
        return RANKS[user.rank_id]  # Следующий ранг
    
    async def get_rank_progress(self, telegram_id: str) -> dict:
        """Получить прогресс до следующего ранга"""
        user = await self.get_user(telegram_id)
        current_rank = get_rank_by_id(user.rank_id)
        next_rank = await self.get_next_rank(telegram_id)
        
        if not next_rank:
            return {
                'current_xp': user.xp,
                'required_xp': current_rank.required_xp,
                'progress': 100,
                'is_max_rank': True
            }
        
        xp_for_next = next_rank.required_xp - current_rank.required_xp
        xp_progress = user.xp - current_rank.required_xp
        progress = int((xp_progress / xp_for_next) * 100) if xp_for_next > 0 else 0
        
        return {
            'current_xp': user.xp,
            'required_xp': next_rank.required_xp,
            'xp_to_next': next_rank.required_xp - user.xp,
            'progress': progress,
            'is_max_rank': False
        }
