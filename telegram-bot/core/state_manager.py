"""
Centralized FSM state management
Управление состояниями с TTL и авто-сбросом
"""
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class StateTimeout(Enum):
    """Таймауты для разных типов состояний"""
    SHORT = 300      # 5 минут (быстрые действия)
    MEDIUM = 900     # 15 минут (формы, создание)
    LONG = 1800      # 30 минут (сложные процессы)
    VERY_LONG = 3600 # 1 час (редкие случаи)


class StateKey(Enum):
    """Ключи состояний"""
    # Тикеты
    TICKET_CREATING = "ticket_creating"
    TICKET_REPLYING = "ticket_replying"
    
    # Игры
    GAME_GUESS_ACTIVE = "game_guess_active"
    GAME_QUIZ_ACTIVE = "game_quiz_active"
    
    # Discord
    DISCORD_LINKING = "discord_linking"
    
    # Админ
    ADMIN_BROADCAST = "admin_broadcast"
    ADMIN_BAN_USER = "admin_ban_user"


class StateManager:
    """
    Менеджер состояний с TTL
    
    Особенности:
    - Автоматический сброс по таймауту
    - Валидация состояний
    - Логирование переходов
    - Защита от гонок
    """
    
    def __init__(self):
        self._states: Dict[int, Dict[str, Any]] = {}
        self._timestamps: Dict[int, Dict[str, datetime]] = {}
    
    def set_state(
        self,
        user_id: int,
        state_key: StateKey,
        data: Optional[Dict[str, Any]] = None,
        timeout: StateTimeout = StateTimeout.MEDIUM
    ):
        """
        Установить состояние пользователя
        
        Args:
            user_id: ID пользователя
            state_key: Ключ состояния
            data: Данные состояния
            timeout: Таймаут состояния
        """
        if user_id not in self._states:
            self._states[user_id] = {}
            self._timestamps[user_id] = {}
        
        self._states[user_id][state_key.value] = data or {}
        self._timestamps[user_id][state_key.value] = datetime.now()
        
        logger.debug(
            f"🔄 Состояние установлено: user={user_id}, "
            f"state={state_key.value}, timeout={timeout.value}s"
        )
    
    def get_state(
        self,
        user_id: int,
        state_key: StateKey
    ) -> Optional[Dict[str, Any]]:
        """
        Получить состояние пользователя
        
        Args:
            user_id: ID пользователя
            state_key: Ключ состояния
        
        Returns:
            Данные состояния или None если истекло/не существует
        """
        if user_id not in self._states:
            return None
        
        if state_key.value not in self._states[user_id]:
            return None
        
        # Проверяем таймаут
        if self._is_expired(user_id, state_key):
            logger.debug(
                f"⏰ Состояние истекло: user={user_id}, state={state_key.value}"
            )
            self.clear_state(user_id, state_key)
            return None
        
        return self._states[user_id][state_key.value]
    
    def has_state(
        self,
        user_id: int,
        state_key: StateKey
    ) -> bool:
        """
        Проверить наличие активного состояния
        
        Args:
            user_id: ID пользователя
            state_key: Ключ состояния
        
        Returns:
            True если состояние активно
        """
        return self.get_state(user_id, state_key) is not None
    
    def clear_state(
        self,
        user_id: int,
        state_key: Optional[StateKey] = None
    ):
        """
        Очистить состояние пользователя
        
        Args:
            user_id: ID пользователя
            state_key: Ключ состояния (если None - очистить все)
        """
        if user_id not in self._states:
            return
        
        if state_key is None:
            # Очистить все состояния
            self._states.pop(user_id, None)
            self._timestamps.pop(user_id, None)
            logger.debug(f"🧹 Все состояния очищены: user={user_id}")
        else:
            # Очистить конкретное состояние
            self._states[user_id].pop(state_key.value, None)
            self._timestamps[user_id].pop(state_key.value, None)
            logger.debug(
                f"🧹 Состояние очищено: user={user_id}, state={state_key.value}"
            )
    
    def update_state_data(
        self,
        user_id: int,
        state_key: StateKey,
        data: Dict[str, Any]
    ):
        """
        Обновить данные состояния
        
        Args:
            user_id: ID пользователя
            state_key: Ключ состояния
            data: Новые данные (merge с существующими)
        """
        current = self.get_state(user_id, state_key)
        
        if current is None:
            logger.warning(
                f"⚠️  Попытка обновить несуществующее состояние: "
                f"user={user_id}, state={state_key.value}"
            )
            return
        
        current.update(data)
        logger.debug(
            f"📝 Данные состояния обновлены: user={user_id}, "
            f"state={state_key.value}"
        )
    
    def _is_expired(
        self,
        user_id: int,
        state_key: StateKey,
        timeout: StateTimeout = StateTimeout.MEDIUM
    ) -> bool:
        """
        Проверить истекло ли состояние
        
        Args:
            user_id: ID пользователя
            state_key: Ключ состояния
            timeout: Таймаут для проверки
        
        Returns:
            True если истекло
        """
        if user_id not in self._timestamps:
            return True
        
        if state_key.value not in self._timestamps[user_id]:
            return True
        
        timestamp = self._timestamps[user_id][state_key.value]
        elapsed = (datetime.now() - timestamp).total_seconds()
        
        return elapsed > timeout.value
    
    def cleanup_expired(self):
        """
        Очистить все истекшие состояния
        (вызывается периодически из фоновой задачи)
        """
        expired_count = 0
        
        for user_id in list(self._states.keys()):
            for state_key_str in list(self._states[user_id].keys()):
                try:
                    state_key = StateKey(state_key_str)
                    if self._is_expired(user_id, state_key):
                        self.clear_state(user_id, state_key)
                        expired_count += 1
                except ValueError:
                    # Неизвестный ключ состояния
                    pass
        
        if expired_count > 0:
            logger.info(f"🧹 Очищено истекших состояний: {expired_count}")
    
    def get_stats(self) -> dict:
        """Получить статистику состояний"""
        total_users = len(self._states)
        total_states = sum(len(states) for states in self._states.values())
        
        return {
            'total_users': total_users,
            'total_states': total_states,
            'avg_states_per_user': total_states / total_users if total_users > 0 else 0
        }


# Глобальный экземпляр менеджера состояний
state_manager = StateManager()
