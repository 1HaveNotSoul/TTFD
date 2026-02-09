# 🚀 TTFD Telegram Platform Evolution Roadmap

**Версия:** 3.0 → 5.0  
**Цель:** Превратить базовый бот в полноценную платформу (community + support + game + economy + automation)  
**Подход:** Эволюционное расширение, не переписывание с нуля  
**Масштаб:** 50k+ пользователей, множество админов, веб-панель

---

## 📊 АУДИТ ТЕКУЩЕЙ СТРУКТУРЫ (v2.1)

### ✅ Что уже есть:
- **Архитектура:** Базовая модульная структура (handlers, utils)
- **Функционал:** Профиль, XP, монеты, 20 рангов, магазин, тикеты, игры
- **FSM:** ConversationHandler для тикетов и игр
- **Хранилище:** JSON (user_data.json, tickets.json, shop.json)
- **Деплой:** Railway, Python 3.11.9, python-telegram-bot 20.7

### ❌ Проблемы текущей архитектуры:
1. **Монолитные handlers** - вся логика в обработчиках
2. **JSON не масштабируется** - race conditions, медленный поиск
3. **Нет слоя бизнес-логики** - handlers = god-objects
4. **Нет ролей и permissions** - только admin/user
5. **Примитивная экономика** - одна валюта, нет анти-абьюза
6. **Игры без глубины** - нет PvP, турниров, сезонов
7. **Тикеты без SLA** - нет приоритетов, статистики
8. **Нет автоматизации** - нет cron-задач, фоновых процессов
9. **Нет кэширования** - каждый запрос = чтение JSON
10. **Нет аналитики** - нет метрик, логов, мониторинга

---

## 🎯 ROADMAP: 5 ЭТАПОВ ЭВОЛЮЦИИ


### 🔷 ЭТАП 1: АРХИТЕКТУРНЫЙ РЕФАКТОРИНГ (v3.0)
**Срок:** 2-3 недели  
**Цель:** Создать масштабируемую архитектуру без изменения функционала

#### 1.1 Новая структура каталогов
```
telegram-bot/
├── core/                      # Ядро системы
│   ├── __init__.py
│   ├── bot.py                # Инициализация бота
│   ├── config.py             # Конфигурация
│   └── exceptions.py         # Кастомные исключения
│
├── domain/                    # Бизнес-логика (Domain Layer)
│   ├── __init__.py
│   ├── models/               # Модели данных
│   │   ├── user.py          # User, UserProfile, UserStats
│   │   ├── economy.py       # Currency, Transaction, Item
│   │   ├── game.py          # Game, Tournament, Season
│   │   └── ticket.py        # Ticket, TicketMessage, SLA
│   │
│   ├── services/            # Бизнес-логика
│   │   ├── user_service.py
│   │   ├── economy_service.py
│   │   ├── game_service.py
│   │   ├── ticket_service.py
│   │   └── achievement_service.py
│   │
│   └── events/              # Доменные события
│       ├── user_events.py
│       └── game_events.py
│
├── infrastructure/           # Инфраструктура
│   ├── __init__.py
│   ├── database/
│   │   ├── repositories/    # Репозитории (Data Access)
│   │   │   ├── user_repository.py
│   │   │   ├── economy_repository.py
│   │   │   └── ticket_repository.py
│   │   ├── migrations/      # Миграции БД
│   │   └── connection.py    # Подключение к БД
│   │
│   ├── cache/               # Кэширование
│   │   ├── redis_cache.py
│   │   └── memory_cache.py
│   │
│   └── external/            # Внешние сервисы
│       ├── discord_api.py
│       └── ai_service.py
│
├── application/             # Application Layer
│   ├── __init__.py
│   ├── handlers/           # Telegram handlers (тонкий слой)
│   │   ├── user/
│   │   │   ├── profile_handler.py
│   │   │   └── settings_handler.py
│   │   ├── economy/
│   │   │   ├── shop_handler.py
│   │   │   └── daily_handler.py
│   │   ├── games/
│   │   │   ├── guess_handler.py
│   │   │   └── tournament_handler.py
│   │   └── support/
│   │       └── ticket_handler.py
│   │
│   ├── middlewares/        # Middleware
│   │   ├── auth_middleware.py
│   │   ├── rate_limit_middleware.py
│   │   └── logging_middleware.py
│   │
│   └── jobs/               # Фоновые задачи
│       ├── daily_reset_job.py
│       ├── tournament_job.py
│       └── cleanup_job.py
│
├── presentation/           # UI Layer
│   ├── __init__.py
│   ├── keyboards/         # Клавиатуры
│   │   ├── main_menu.py
│   │   ├── game_menu.py
│   │   └── admin_menu.py
│   │
│   └── messages/          # Шаблоны сообщений
│       ├── user_messages.py
│       └── game_messages.py
│
├── tests/                 # Тесты
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── data/                  # Данные (временно)
├── logs/                  # Логи
├── main.py               # Точка входа
├── requirements.txt
└── .env
```

#### 1.2 Принципы новой архитектуры

**Clean Architecture + DDD (Domain-Driven Design):**
- **Domain Layer** - бизнес-логика, не зависит от фреймворков
- **Application Layer** - оркестрация, handlers как тонкий слой
- **Infrastructure Layer** - БД, кэш, внешние API
- **Presentation Layer** - UI, клавиатуры, сообщения

**Где должна быть бизнес-логика:**
- ❌ НЕ в handlers (handlers только маршрутизация)
- ✅ В services (domain/services/)
- ✅ В models (domain/models/)

**Как избежать god-handlers:**
- Handlers вызывают services
- Services содержат бизнес-логику
- Repositories работают с БД
- Models - чистые данные + валидация


#### 1.3 Пример рефакторинга: Профиль пользователя

**Было (v2.1):**
```python
# handlers/commands.py - ВСЯ логика в handler
async def profile_command(update: Update, context):
    user = db.get_user(update.effective_user.id)
    rank = db.get_rank_info(user['rank_id'])
    # ... форматирование сообщения
    await update.message.reply_text(text)
```

**Стало (v3.0):**
```python
# domain/models/user.py
@dataclass
class User:
    telegram_id: str
    username: str
    xp: int
    coins: int
    rank_id: int
    created_at: datetime
    
    def can_level_up(self, ranks: List[Rank]) -> bool:
        """Бизнес-логика: может ли повыситься"""
        pass

# domain/services/user_service.py
class UserService:
    def __init__(self, user_repo: UserRepository, rank_repo: RankRepository):
        self.user_repo = user_repo
        self.rank_repo = rank_repo
    
    async def get_user_profile(self, telegram_id: str) -> UserProfile:
        """Бизнес-логика получения профиля"""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        rank = await self.rank_repo.get_by_id(user.rank_id)
        next_rank = await self.rank_repo.get_next_rank(user.rank_id)
        
        return UserProfile(
            user=user,
            rank=rank,
            next_rank=next_rank,
            progress=self._calculate_progress(user, next_rank)
        )

# application/handlers/user/profile_handler.py
class ProfileHandler:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def handle_profile_command(self, update: Update, context):
        """Тонкий слой: маршрутизация + UI"""
        profile = await self.user_service.get_user_profile(
            str(update.effective_user.id)
        )
        
        message = ProfileMessageFormatter.format(profile)
        keyboard = ProfileKeyboard.create(profile)
        
        await update.message.reply_text(message, reply_markup=keyboard)
```

**Преимущества:**
- Бизнес-логика тестируется отдельно
- Handler не знает о БД
- Service переиспользуется (Telegram, Web API, Discord)
- Легко добавить кэширование в repository

---

### 🔷 ЭТАП 2: МИГРАЦИЯ НА PostgreSQL + КЭШИРОВАНИЕ (v3.5)
**Срок:** 1-2 недели  
**Цель:** Масштабируемое хранилище данных

#### 2.1 Миграция JSON → PostgreSQL

**Схема БД:**
```sql
-- Пользователи
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    xp INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    rank_id INTEGER DEFAULT 1,
    discord_id VARCHAR(50),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    last_daily TIMESTAMP,
    last_spin TIMESTAMP,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT
);

-- Экономика: Транзакции
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50), -- 'daily', 'game_win', 'shop_purchase', 'admin_grant'
    amount INTEGER,
    currency VARCHAR(20) DEFAULT 'coins',
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Экономика: Инвентарь
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    item_id INTEGER,
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

-- Игры: История
CREATE TABLE game_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    game_type VARCHAR(50),
    bet_amount INTEGER,
    win_amount INTEGER,
    result VARCHAR(20), -- 'win', 'lose', 'draw'
    details JSONB,
    played_at TIMESTAMP DEFAULT NOW()
);

-- Тикеты
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    subject TEXT,
    assigned_to INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    sla_deadline TIMESTAMP
);

CREATE TABLE ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id),
    user_id INTEGER REFERENCES users(id),
    message TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Достижения
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    name VARCHAR(100),
    description TEXT,
    reward_xp INTEGER,
    reward_coins INTEGER,
    icon VARCHAR(50)
);

CREATE TABLE user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    achievement_id INTEGER REFERENCES achievements(id),
    unlocked_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- Индексы для производительности
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_xp ON users(xp DESC);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_assigned ON tickets(assigned_to);
```


#### 2.2 Repository Pattern

```python
# infrastructure/database/repositories/user_repository.py
from typing import Optional, List
import asyncpg

class UserRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            return User.from_db_row(row) if row else None
    
    async def create(self, user: User) -> User:
        """Создать пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (telegram_id, username, first_name)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                user.telegram_id, user.username, user.first_name
            )
            return User.from_db_row(row)
    
    async def update_xp(self, user_id: int, xp_delta: int) -> User:
        """Обновить XP (атомарно)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE users 
                SET xp = xp + $1, last_active = NOW()
                WHERE id = $2
                RETURNING *
                """,
                xp_delta, user_id
            )
            return User.from_db_row(row)
    
    async def get_leaderboard(self, limit: int = 10) -> List[User]:
        """Топ пользователей по XP"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM users ORDER BY xp DESC LIMIT $1",
                limit
            )
            return [User.from_db_row(row) for row in rows]
```

#### 2.3 Кэширование (Redis)

```python
# infrastructure/cache/redis_cache.py
import redis.asyncio as redis
import json
from typing import Optional, Any

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить из кэша"""
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Сохранить в кэш (TTL в секундах)"""
        await self.redis.setex(key, ttl, json.dumps(value))
    
    async def delete(self, key: str):
        """Удалить из кэша"""
        await self.redis.delete(key)
    
    async def invalidate_pattern(self, pattern: str):
        """Инвалидировать по паттерну"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# domain/services/user_service.py (с кэшированием)
class UserService:
    def __init__(
        self, 
        user_repo: UserRepository,
        cache: RedisCache
    ):
        self.user_repo = user_repo
        self.cache = cache
    
    async def get_user_profile(self, telegram_id: str) -> UserProfile:
        """Получить профиль с кэшированием"""
        cache_key = f"user:profile:{telegram_id}"
        
        # Проверяем кэш
        cached = await self.cache.get(cache_key)
        if cached:
            return UserProfile.from_dict(cached)
        
        # Загружаем из БД
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        profile = await self._build_profile(user)
        
        # Сохраняем в кэш на 5 минут
        await self.cache.set(cache_key, profile.to_dict(), ttl=300)
        
        return profile
    
    async def add_xp(self, telegram_id: str, amount: int):
        """Добавить XP + инвалидировать кэш"""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        await self.user_repo.update_xp(user.id, amount)
        
        # Инвалидируем кэш профиля и лидерборда
        await self.cache.delete(f"user:profile:{telegram_id}")
        await self.cache.invalidate_pattern("leaderboard:*")
```

**Что кэшировать:**
- Профили пользователей (5 мин)
- Лидерборд (1 мин)
- Список товаров магазина (10 мин)
- Конфигурацию игр (30 мин)

---

### 🔷 ЭТАП 3: СИСТЕМА РОЛЕЙ И PERMISSIONS (v4.0)
**Срок:** 1 неделя  
**Цель:** Гибкая система прав доступа

#### 3.1 Роли и права

```python
# domain/models/permission.py
from enum import Enum

class Permission(Enum):
    # Пользовательские
    VIEW_PROFILE = "view_profile"
    EDIT_PROFILE = "edit_profile"
    USE_SHOP = "use_shop"
    PLAY_GAMES = "play_games"
    CREATE_TICKETS = "create_tickets"
    
    # VIP
    VIP_SHOP_ACCESS = "vip_shop_access"
    VIP_DAILY_BONUS = "vip_daily_bonus"
    SKIP_COOLDOWNS = "skip_cooldowns"
    
    # Модератор
    VIEW_TICKETS = "view_tickets"
    ASSIGN_TICKETS = "assign_tickets"
    CLOSE_TICKETS = "close_tickets"
    MUTE_USERS = "mute_users"
    
    # Админ
    MANAGE_USERS = "manage_users"
    MANAGE_ECONOMY = "manage_economy"
    MANAGE_GAMES = "manage_games"
    VIEW_ANALYTICS = "view_analytics"
    BROADCAST = "broadcast"

class Role(Enum):
    USER = "user"
    VIP = "vip"
    MODERATOR = "moderator"
    ADMIN = "admin"
    OWNER = "owner"

# Матрица прав
ROLE_PERMISSIONS = {
    Role.USER: [
        Permission.VIEW_PROFILE,
        Permission.EDIT_PROFILE,
        Permission.USE_SHOP,
        Permission.PLAY_GAMES,
        Permission.CREATE_TICKETS,
    ],
    Role.VIP: [
        # Все права USER +
        *ROLE_PERMISSIONS[Role.USER],
        Permission.VIP_SHOP_ACCESS,
        Permission.VIP_DAILY_BONUS,
        Permission.SKIP_COOLDOWNS,
    ],
    Role.MODERATOR: [
        # Все права VIP +
        *ROLE_PERMISSIONS[Role.VIP],
        Permission.VIEW_TICKETS,
        Permission.ASSIGN_TICKETS,
        Permission.CLOSE_TICKETS,
        Permission.MUTE_USERS,
    ],
    Role.ADMIN: [
        # Все права MODERATOR +
        *ROLE_PERMISSIONS[Role.MODERATOR],
        Permission.MANAGE_USERS,
        Permission.MANAGE_ECONOMY,
        Permission.MANAGE_GAMES,
        Permission.VIEW_ANALYTICS,
        Permission.BROADCAST,
    ],
    Role.OWNER: [
        # Все права
        *[p for p in Permission]
    ]
}

# domain/services/permission_service.py
class PermissionService:
    @staticmethod
    def has_permission(user: User, permission: Permission) -> bool:
        """Проверить право доступа"""
        role = Role(user.role)
        return permission in ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def require_permission(permission: Permission):
        """Декоратор для проверки прав"""
        def decorator(func):
            async def wrapper(self, update: Update, context, *args, **kwargs):
                user = await self.user_service.get_user(
                    str(update.effective_user.id)
                )
                
                if not PermissionService.has_permission(user, permission):
                    await update.message.reply_text(
                        "❌ У тебя нет прав для этого действия"
                    )
                    return
                
                return await func(self, update, context, *args, **kwargs)
            return wrapper
        return decorator
```


#### 3.2 Использование в handlers

```python
# application/handlers/admin/user_management_handler.py
class UserManagementHandler:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    @PermissionService.require_permission(Permission.MANAGE_USERS)
    async def ban_user(self, update: Update, context):
        """Забанить пользователя (только для админов)"""
        # Логика бана
        pass
    
    @PermissionService.require_permission(Permission.VIEW_ANALYTICS)
    async def view_stats(self, update: Update, context):
        """Статистика (только для админов)"""
        # Логика статистики
        pass
```

---

### 🔷 ЭТАП 4: ПРОДВИНУТАЯ ЭКОНОМИКА И ИГРЫ (v4.5)
**Срок:** 2-3 недели  
**Цель:** Глубокая игровая механика

#### 4.1 Мультивалютная экономика

```python
# domain/models/economy.py
from enum import Enum
from decimal import Decimal

class Currency(Enum):
    COINS = "coins"           # Основная валюта
    GEMS = "gems"             # Премиум валюта
    TOKENS = "tokens"         # Игровые токены
    REPUTATION = "reputation" # Репутация

@dataclass
class Wallet:
    user_id: int
    coins: int = 0
    gems: int = 0
    tokens: int = 0
    reputation: int = 0
    
    def has_currency(self, currency: Currency, amount: int) -> bool:
        """Проверить наличие валюты"""
        return getattr(self, currency.value) >= amount
    
    def add_currency(self, currency: Currency, amount: int):
        """Добавить валюту"""
        current = getattr(self, currency.value)
        setattr(self, currency.value, current + amount)
    
    def remove_currency(self, currency: Currency, amount: int) -> bool:
        """Убрать валюту"""
        if not self.has_currency(currency, amount):
            return False
        current = getattr(self, currency.value)
        setattr(self, currency.value, current - amount)
        return True

@dataclass
class Transaction:
    id: int
    user_id: int
    type: str  # 'daily', 'game_win', 'shop_purchase', 'admin_grant'
    currency: Currency
    amount: int
    description: str
    metadata: dict
    created_at: datetime

# domain/services/economy_service.py
class EconomyService:
    def __init__(
        self,
        wallet_repo: WalletRepository,
        transaction_repo: TransactionRepository,
        anti_abuse: AntiAbuseService
    ):
        self.wallet_repo = wallet_repo
        self.transaction_repo = transaction_repo
        self.anti_abuse = anti_abuse
    
    async def transfer_currency(
        self,
        from_user_id: int,
        to_user_id: int,
        currency: Currency,
        amount: int,
        reason: str
    ) -> bool:
        """Перевод валюты между пользователями"""
        
        # Анти-абьюз проверка
        if not await self.anti_abuse.can_transfer(from_user_id, amount):
            raise EconomyError("Превышен лимит переводов")
        
        # Атомарная транзакция
        async with self.wallet_repo.transaction():
            from_wallet = await self.wallet_repo.get(from_user_id)
            to_wallet = await self.wallet_repo.get(to_user_id)
            
            if not from_wallet.remove_currency(currency, amount):
                raise InsufficientFundsError()
            
            to_wallet.add_currency(currency, amount)
            
            await self.wallet_repo.update(from_wallet)
            await self.wallet_repo.update(to_wallet)
            
            # Логируем транзакции
            await self.transaction_repo.create(Transaction(
                user_id=from_user_id,
                type='transfer_out',
                currency=currency,
                amount=-amount,
                description=f"Перевод {to_user_id}: {reason}"
            ))
            
            await self.transaction_repo.create(Transaction(
                user_id=to_user_id,
                type='transfer_in',
                currency=currency,
                amount=amount,
                description=f"Получено от {from_user_id}: {reason}"
            ))
        
        return True
    
    async def apply_tax(self, user_id: int, amount: int) -> int:
        """Применить налог (для больших сумм)"""
        if amount > 10000:
            tax_rate = 0.05  # 5% налог
            tax = int(amount * tax_rate)
            return amount - tax
        return amount
    
    async def apply_cashback(self, user_id: int, purchase_amount: int):
        """Кэшбэк за покупки (для VIP)"""
        user = await self.user_service.get_user(user_id)
        if user.role == Role.VIP:
            cashback = int(purchase_amount * 0.1)  # 10% кэшбэк
            await self.add_currency(user_id, Currency.COINS, cashback)
```

#### 4.2 Анти-абьюз система

```python
# domain/services/anti_abuse_service.py
from datetime import datetime, timedelta

class AntiAbuseService:
    def __init__(self, cache: RedisCache):
        self.cache = cache
    
    async def can_transfer(self, user_id: int, amount: int) -> bool:
        """Проверить лимиты переводов"""
        key = f"transfer_limit:{user_id}"
        
        # Лимит: 5 переводов в час
        transfers = await self.cache.get(key) or []
        recent = [t for t in transfers if t > datetime.now() - timedelta(hours=1)]
        
        if len(recent) >= 5:
            return False
        
        # Лимит: не более 10000 монет в час
        total = sum(t['amount'] for t in recent)
        if total + amount > 10000:
            return False
        
        return True
    
    async def log_transfer(self, user_id: int, amount: int):
        """Залогировать перевод"""
        key = f"transfer_limit:{user_id}"
        transfers = await self.cache.get(key) or []
        transfers.append({
            'amount': amount,
            'timestamp': datetime.now().isoformat()
        })
        await self.cache.set(key, transfers, ttl=3600)
    
    async def detect_suspicious_activity(self, user_id: int) -> bool:
        """Детект подозрительной активности"""
        # Проверяем паттерны:
        # - Слишком много игр подряд
        # - Необычно высокий винрейт
        # - Быстрые переводы между аккаунтами
        pass
```


#### 4.3 Продвинутые игры: PvP, Турниры, Сезоны

```python
# domain/models/game.py
from enum import Enum

class GameMode(Enum):
    PVE = "pve"  # Против бота
    PVP = "pvp"  # Против игрока
    TOURNAMENT = "tournament"

@dataclass
class Game:
    id: int
    type: str  # 'guess', 'quiz', 'duel'
    mode: GameMode
    player1_id: int
    player2_id: Optional[int]
    bet_amount: int
    currency: Currency
    status: str  # 'waiting', 'active', 'finished'
    winner_id: Optional[int]
    created_at: datetime
    finished_at: Optional[datetime]

@dataclass
class Tournament:
    id: int
    name: str
    game_type: str
    entry_fee: int
    prize_pool: int
    max_players: int
    current_players: int
    status: str  # 'registration', 'active', 'finished'
    starts_at: datetime
    ends_at: datetime
    bracket: dict  # Турнирная сетка

@dataclass
class Season:
    id: int
    number: int
    name: str
    starts_at: datetime
    ends_at: datetime
    rewards: dict  # Награды по местам

# domain/services/game_service.py
class GameService:
    async def create_pvp_game(
        self,
        player1_id: int,
        game_type: str,
        bet_amount: int
    ) -> Game:
        """Создать PvP игру (ожидание оппонента)"""
        
        # Проверяем баланс
        wallet = await self.wallet_repo.get(player1_id)
        if not wallet.has_currency(Currency.COINS, bet_amount):
            raise InsufficientFundsError()
        
        # Замораживаем ставку
        await self.economy_service.freeze_currency(
            player1_id, Currency.COINS, bet_amount
        )
        
        # Создаём игру
        game = await self.game_repo.create(Game(
            type=game_type,
            mode=GameMode.PVP,
            player1_id=player1_id,
            bet_amount=bet_amount,
            currency=Currency.COINS,
            status='waiting'
        ))
        
        # Добавляем в очередь поиска
        await self.matchmaking_service.add_to_queue(game)
        
        return game
    
    async def join_pvp_game(self, player2_id: int, game_id: int):
        """Присоединиться к PvP игре"""
        game = await self.game_repo.get(game_id)
        
        if game.status != 'waiting':
            raise GameError("Игра уже началась")
        
        # Проверяем баланс
        wallet = await self.wallet_repo.get(player2_id)
        if not wallet.has_currency(game.currency, game.bet_amount):
            raise InsufficientFundsError()
        
        # Замораживаем ставку
        await self.economy_service.freeze_currency(
            player2_id, game.currency, game.bet_amount
        )
        
        # Обновляем игру
        game.player2_id = player2_id
        game.status = 'active'
        await self.game_repo.update(game)
        
        # Уведомляем игроков
        await self.notification_service.notify_game_start(game)
        
        return game
    
    async def finish_game(self, game_id: int, winner_id: int):
        """Завершить игру и распределить награды"""
        game = await self.game_repo.get(game_id)
        
        # Обновляем статус
        game.status = 'finished'
        game.winner_id = winner_id
        game.finished_at = datetime.now()
        await self.game_repo.update(game)
        
        # Распределяем награды
        total_pot = game.bet_amount * 2
        winner_reward = int(total_pot * 0.95)  # 5% комиссия платформы
        
        await self.economy_service.unfreeze_and_add(
            winner_id, game.currency, winner_reward
        )
        
        # Размораживаем проигравшему (но не возвращаем)
        loser_id = game.player1_id if winner_id == game.player2_id else game.player2_id
        await self.economy_service.unfreeze_currency(
            loser_id, game.currency, game.bet_amount
        )
        
        # Обновляем статистику
        await self.stats_service.record_game_result(game)
        
        # Уведомляем игроков
        await self.notification_service.notify_game_end(game)

# domain/services/tournament_service.py
class TournamentService:
    async def create_tournament(
        self,
        name: str,
        game_type: str,
        entry_fee: int,
        max_players: int,
        starts_at: datetime
    ) -> Tournament:
        """Создать турнир"""
        tournament = await self.tournament_repo.create(Tournament(
            name=name,
            game_type=game_type,
            entry_fee=entry_fee,
            prize_pool=0,
            max_players=max_players,
            current_players=0,
            status='registration',
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2)
        ))
        
        return tournament
    
    async def register_player(self, tournament_id: int, user_id: int):
        """Зарегистрировать игрока в турнире"""
        tournament = await self.tournament_repo.get(tournament_id)
        
        if tournament.status != 'registration':
            raise TournamentError("Регистрация закрыта")
        
        if tournament.current_players >= tournament.max_players:
            raise TournamentError("Турнир заполнен")
        
        # Списываем взнос
        await self.economy_service.remove_currency(
            user_id, Currency.COINS, tournament.entry_fee
        )
        
        # Добавляем в призовой фонд
        tournament.prize_pool += tournament.entry_fee
        tournament.current_players += 1
        
        await self.tournament_repo.update(tournament)
        await self.tournament_repo.add_participant(tournament_id, user_id)
        
        return tournament
    
    async def start_tournament(self, tournament_id: int):
        """Запустить турнир (создать сетку)"""
        tournament = await self.tournament_repo.get(tournament_id)
        participants = await self.tournament_repo.get_participants(tournament_id)
        
        # Создаём турнирную сетку (single elimination)
        bracket = self._create_bracket(participants)
        
        tournament.status = 'active'
        tournament.bracket = bracket
        await self.tournament_repo.update(tournament)
        
        # Создаём первые матчи
        await self._create_first_round_matches(tournament, bracket)
```


---

### 🔷 ЭТАП 5: АВТОМАТИЗАЦИЯ И AI (v5.0)
**Срок:** 2 недели  
**Цель:** Фоновые процессы и AI-интеграция

#### 5.1 Job System (APScheduler)

```python
# application/jobs/base_job.py
from abc import ABC, abstractmethod

class BaseJob(ABC):
    @abstractmethod
    async def execute(self):
        """Выполнить задачу"""
        pass
    
    @abstractmethod
    def get_schedule(self) -> str:
        """Расписание (cron)"""
        pass

# application/jobs/daily_reset_job.py
class DailyResetJob(BaseJob):
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def execute(self):
        """Сброс ежедневных лимитов"""
        print("🔄 Запуск ежедневного сброса...")
        
        # Сбрасываем кулдауны
        await self.user_service.reset_daily_cooldowns()
        
        # Начисляем пассивный доход VIP
        vip_users = await self.user_service.get_vip_users()
        for user in vip_users:
            await self.economy_service.add_currency(
                user.id, Currency.COINS, 100
            )
        
        print("✅ Ежедневный сброс завершён")
    
    def get_schedule(self) -> str:
        return "0 0 * * *"  # Каждый день в 00:00

# application/jobs/tournament_job.py
class TournamentJob(BaseJob):
    def __init__(self, tournament_service: TournamentService):
        self.tournament_service = tournament_service
    
    async def execute(self):
        """Проверка и запуск турниров"""
        now = datetime.now()
        
        # Запускаем турниры, которые должны начаться
        pending = await self.tournament_service.get_pending_tournaments(now)
        for tournament in pending:
            await self.tournament_service.start_tournament(tournament.id)
        
        # Завершаем турниры, которые должны закончиться
        active = await self.tournament_service.get_active_tournaments(now)
        for tournament in active:
            if tournament.ends_at <= now:
                await self.tournament_service.finish_tournament(tournament.id)
    
    def get_schedule(self) -> str:
        return "*/5 * * * *"  # Каждые 5 минут

# application/jobs/cleanup_job.py
class CleanupJob(BaseJob):
    async def execute(self):
        """Очистка старых данных"""
        # Удаляем старые логи (> 30 дней)
        await self.log_repo.delete_older_than(days=30)
        
        # Удаляем закрытые тикеты (> 90 дней)
        await self.ticket_repo.delete_closed_older_than(days=90)
        
        # Очищаем expired items из инвентаря
        await self.inventory_repo.delete_expired()
    
    def get_schedule(self) -> str:
        return "0 3 * * *"  # Каждый день в 03:00

# core/job_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class JobScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs = []
    
    def register_job(self, job: BaseJob):
        """Зарегистрировать задачу"""
        self.jobs.append(job)
        
        trigger = CronTrigger.from_crontab(job.get_schedule())
        self.scheduler.add_job(
            job.execute,
            trigger=trigger,
            id=job.__class__.__name__
        )
    
    def start(self):
        """Запустить планировщик"""
        print("🕐 Запуск планировщика задач...")
        for job in self.jobs:
            print(f"   • {job.__class__.__name__}: {job.get_schedule()}")
        self.scheduler.start()
    
    def stop(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()

# main.py
async def main():
    # ... инициализация сервисов
    
    # Регистрируем фоновые задачи
    scheduler = JobScheduler()
    scheduler.register_job(DailyResetJob(user_service))
    scheduler.register_job(TournamentJob(tournament_service))
    scheduler.register_job(CleanupJob())
    scheduler.start()
    
    # Запускаем бота
    app.run_polling()
```

#### 5.2 AI-интеграция (OpenAI GPT)

```python
# infrastructure/external/ai_service.py
import openai
from typing import Optional

class AIService:
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.model = "gpt-4o-mini"  # Дешёвая модель
    
    async def generate_ticket_response(
        self,
        ticket: Ticket,
        messages: List[TicketMessage]
    ) -> str:
        """Сгенерировать черновик ответа на тикет"""
        
        # Формируем контекст
        context = f"""
        Категория: {ticket.category}
        Приоритет: {ticket.priority}
        
        История сообщений:
        """
        for msg in messages:
            role = "Админ" if msg.is_admin else "Пользователь"
            context += f"\n{role}: {msg.message}"
        
        # Запрос к AI
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Ты - помощник техподдержки. Генерируй краткие, полезные ответы."
                },
                {
                    "role": "user",
                    "content": f"{context}\n\nСгенерируй черновик ответа:"
                }
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    async def analyze_user_behavior(self, user_id: int) -> dict:
        """Анализ поведения пользователя"""
        
        # Получаем историю активности
        activity = await self.analytics_service.get_user_activity(user_id)
        
        # Анализируем паттерны
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Анализируй поведение пользователей и выявляй паттерны."
                },
                {
                    "role": "user",
                    "content": f"Активность пользователя: {activity}\n\nВыяви паттерны:"
                }
            ],
            max_tokens=150
        )
        
        return {
            'analysis': response.choices[0].message.content,
            'risk_level': self._calculate_risk(activity)
        }
    
    async def generate_quest(self, difficulty: str) -> dict:
        """Сгенерировать квест"""
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Генерируй интересные квесты для игроков."
                },
                {
                    "role": "user",
                    "content": f"Создай квест сложности {difficulty}"
                }
            ],
            max_tokens=300
        )
        
        return {
            'title': '...',
            'description': response.choices[0].message.content,
            'reward': self._calculate_reward(difficulty)
        }

# Ограничение стоимости AI
class AIRateLimiter:
    def __init__(self, cache: RedisCache):
        self.cache = cache
        self.max_requests_per_hour = 100  # Лимит запросов
        self.max_cost_per_day = 5.0  # Лимит $5/день
    
    async def can_make_request(self, user_id: int) -> bool:
        """Проверить лимиты"""
        # Проверяем количество запросов
        key = f"ai:requests:{user_id}"
        requests = await self.cache.get(key) or 0
        
        if requests >= self.max_requests_per_hour:
            return False
        
        # Проверяем стоимость
        cost_key = "ai:daily_cost"
        daily_cost = await self.cache.get(cost_key) or 0.0
        
        if daily_cost >= self.max_cost_per_day:
            return False
        
        return True
    
    async def log_request(self, user_id: int, cost: float):
        """Залогировать запрос"""
        # Увеличиваем счётчик запросов
        key = f"ai:requests:{user_id}"
        requests = await self.cache.get(key) or 0
        await self.cache.set(key, requests + 1, ttl=3600)
        
        # Увеличиваем стоимость
        cost_key = "ai:daily_cost"
        daily_cost = await self.cache.get(cost_key) or 0.0
        await self.cache.set(cost_key, daily_cost + cost, ttl=86400)
```


---

## 🎯 ПРИОРИТИЗАЦИЯ ФИЧЕЙ

### Must Have (Критично для v3.0)
1. ✅ Архитектурный рефакторинг (Clean Architecture)
2. ✅ Миграция на PostgreSQL
3. ✅ Система ролей и permissions
4. ✅ Кэширование (Redis)
5. ✅ Repository pattern

### Should Have (Важно для v4.0)
6. ✅ Мультивалютная экономика
7. ✅ Анти-абьюз система
8. ✅ PvP игры
9. ✅ Турниры
10. ✅ Продвинутая тикет-система (SLA)

### Could Have (Желательно для v5.0)
11. ✅ AI-интеграция
12. ✅ Сезоны и рейтинги
13. ✅ Достижения
14. ✅ Инвентарь с предметами
15. ✅ Веб-панель (FastAPI)

### Won't Have (Не сейчас)
- Голосовые чаты
- NFT интеграция
- Блокчейн
- Мобильное приложение

---

## 📐 АРХИТЕКТУРНАЯ СХЕМА

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Telegram   │  │   Web API    │  │   Discord    │      │
│  │   Handlers   │  │   (FastAPI)  │  │   Webhook    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Middlewares │  │     Jobs     │  │    Events    │      │
│  │  (Auth, Log) │  │  (Scheduler) │  │  (EventBus)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Services   │  │    Models    │  │    Events    │      │
│  │  (Business)  │  │   (Entities) │  │   (Domain)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │     Redis    │  │   External   │      │
│  │ (Repositories)│  │    (Cache)   │  │  (AI, APIs)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 ПОТОКИ ПОЛЬЗОВАТЕЛЬСКИХ СЦЕНАРИЕВ

### Сценарий 1: Игра в PvP

```
1. Пользователь нажимает "🎮 Игры" → "⚔️ PvP Дуэль"
   ↓
2. Handler → GameService.create_pvp_game()
   ↓
3. GameService проверяет:
   - Баланс пользователя (EconomyService)
   - Нет ли активных игр (GameRepository)
   - Не забанен ли (PermissionService)
   ↓
4. Замораживаем ставку (EconomyService.freeze_currency)
   ↓
5. Создаём игру в БД (GameRepository.create)
   ↓
6. Добавляем в очередь поиска (MatchmakingService)
   ↓
7. Уведомляем пользователя: "⏳ Ищем оппонента..."
   ↓
8. Когда находится оппонент:
   - MatchmakingService.match_players()
   - Замораживаем ставку второго игрока
   - Обновляем статус игры → 'active'
   - Уведомляем обоих игроков
   ↓
9. Игра идёт (FSM ConversationHandler)
   ↓
10. Завершение:
    - GameService.finish_game(winner_id)
    - Распределяем награды (EconomyService)
    - Обновляем статистику (StatsService)
    - Проверяем достижения (AchievementService)
    - Уведомляем игроков
```

### Сценарий 2: Создание тикета с AI-помощью

```
1. Пользователь: "📩 Тикеты" → "➕ Создать"
   ↓
2. FSM: Выбор категории
   ↓
3. FSM: Ввод текста проблемы
   ↓
4. AI анализирует текст:
   - AIService.analyze_ticket_text()
   - Определяет приоритет автоматически
   - Предлагает FAQ если есть похожие
   ↓
5. Если FAQ не помог → создаём тикет:
   - TicketService.create_ticket()
   - Автоматически назначаем админа (SLA)
   - Уведомляем админа
   ↓
6. Админ отвечает:
   - AI генерирует черновик (AIService.generate_response)
   - Админ редактирует и отправляет
   ↓
7. Пользователь получает уведомление
   ↓
8. Закрытие тикета:
   - TicketService.close_ticket()
   - Запрос оценки (1-5 звёзд)
   - Обновление статистики саппорта
```

---

## 🛡️ EDGE-CASES И ЗАЩИТА ОТ АБЬЮЗА

### 1. Race Conditions
**Проблема:** Два запроса одновременно списывают монеты
**Решение:**
```python
# Используем транзакции БД
async with self.wallet_repo.transaction():
    wallet = await self.wallet_repo.get_for_update(user_id)  # SELECT FOR UPDATE
    if wallet.coins >= amount:
        wallet.coins -= amount
        await self.wallet_repo.update(wallet)
```

### 2. Спам игр
**Проблема:** Пользователь создаёт 100 игр в секунду
**Решение:**
```python
# Rate limiting через middleware
class RateLimitMiddleware:
    async def __call__(self, update, context):
        user_id = update.effective_user.id
        key = f"rate_limit:{user_id}"
        
        requests = await cache.get(key) or 0
        if requests > 10:  # 10 запросов в минуту
            await update.message.reply_text("⏱️ Слишком быстро! Подожди немного")
            return
        
        await cache.set(key, requests + 1, ttl=60)
        return await next_handler(update, context)
```

### 3. Накрутка винрейта
**Проблема:** Пользователь создаёт фейковые аккаунты и играет сам с собой
**Решение:**
```python
class AntiAbuseService:
    async def detect_multi_accounting(self, user_id: int) -> bool:
        """Детект мультиаккаунтинга"""
        # Проверяем:
        # - IP адреса (если доступны)
        # - Паттерны игр (всегда играет с одним и тем же)
        # - Время создания аккаунтов
        # - Паттерны переводов
        
        recent_games = await self.game_repo.get_recent_games(user_id, limit=20)
        opponents = [g.player2_id for g in recent_games]
        
        # Если 80%+ игр с одним оппонентом - подозрительно
        if len(set(opponents)) == 1 and len(opponents) > 10:
            await self.flag_suspicious_activity(user_id)
            return True
        
        return False
```

### 4. Эксплойт экономики
**Проблема:** Пользователь находит способ дублировать монеты
**Решение:**
```python
# Логируем ВСЕ транзакции
class TransactionLogger:
    async def log_transaction(self, transaction: Transaction):
        """Логируем каждую транзакцию"""
        await self.transaction_repo.create(transaction)
        
        # Проверяем аномалии
        if transaction.amount > 10000:
            await self.alert_admins(f"Большая транзакция: {transaction}")
        
        # Проверяем баланс пользователя
        wallet = await self.wallet_repo.get(transaction.user_id)
        if wallet.coins < 0:
            # КРИТИЧЕСКАЯ ОШИБКА
            await self.emergency_freeze_account(transaction.user_id)
            await self.alert_admins(f"ОТРИЦАТЕЛЬНЫЙ БАЛАНС: {transaction.user_id}")
```

### 5. DDoS через ботов
**Проблема:** Кто-то создаёт 1000 ботов и спамит команды
**Решение:**
```python
# Глобальный rate limiter
class GlobalRateLimiter:
    async def check_global_rate(self):
        """Проверить глобальную нагрузку"""
        key = "global:requests"
        requests = await cache.get(key) or 0
        
        if requests > 1000:  # 1000 запросов в минуту
            # Включаем защитный режим
            await self.enable_protection_mode()
            return False
        
        await cache.set(key, requests + 1, ttl=60)
        return True
    
    async def enable_protection_mode(self):
        """Защитный режим: только для проверенных пользователей"""
        await cache.set("protection_mode", True, ttl=300)
        await self.notify_admins("⚠️ Включён защитный режим (высокая нагрузка)")
```


---

## 📊 МЕТРИКИ И МОНИТОРИНГ

### Ключевые метрики

```python
# infrastructure/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Метрики пользователей
users_total = Gauge('users_total', 'Всего пользователей')
users_active_daily = Gauge('users_active_daily', 'Активных за день')
users_online = Gauge('users_online', 'Онлайн сейчас')

# Метрики игр
games_played = Counter('games_played_total', 'Всего игр сыграно', ['game_type'])
games_duration = Histogram('games_duration_seconds', 'Длительность игр', ['game_type'])
games_active = Gauge('games_active', 'Активных игр', ['game_type'])

# Метрики экономики
transactions_total = Counter('transactions_total', 'Всего транзакций', ['type'])
coins_in_circulation = Gauge('coins_in_circulation', 'Монет в обороте')
daily_revenue = Counter('daily_revenue', 'Дневной доход')

# Метрики тикетов
tickets_created = Counter('tickets_created_total', 'Создано тикетов')
tickets_resolved = Counter('tickets_resolved_total', 'Решено тикетов')
ticket_response_time = Histogram('ticket_response_time_seconds', 'Время ответа')
tickets_open = Gauge('tickets_open', 'Открытых тикетов')

# Метрики производительности
request_duration = Histogram('request_duration_seconds', 'Время обработки', ['handler'])
db_query_duration = Histogram('db_query_duration_seconds', 'Время запросов к БД', ['query'])
cache_hits = Counter('cache_hits_total', 'Попадания в кэш')
cache_misses = Counter('cache_misses_total', 'Промахи кэша')

# Метрики ошибок
errors_total = Counter('errors_total', 'Всего ошибок', ['type'])
```

### Дашборд (Grafana)

```yaml
# docker-compose.yml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/ttfd
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: ttfd
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
  
  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

## 🚀 ПЛАН МИГРАЦИИ (v2.1 → v3.0)

### Неделя 1: Подготовка
- [ ] Создать новую структуру каталогов
- [ ] Настроить PostgreSQL (локально + Railway)
- [ ] Настроить Redis (локально + Railway)
- [ ] Написать миграцию JSON → PostgreSQL

### Неделя 2: Рефакторинг Core
- [ ] Создать domain/models (User, Wallet, Game, Ticket)
- [ ] Создать infrastructure/repositories
- [ ] Создать domain/services (UserService, EconomyService)
- [ ] Написать unit-тесты для services

### Неделя 3: Рефакторинг Handlers
- [ ] Переписать handlers/commands.py → application/handlers/user/
- [ ] Переписать handlers/games.py → application/handlers/games/
- [ ] Переписать handlers/tickets.py → application/handlers/support/
- [ ] Добавить middlewares (auth, rate_limit, logging)

### Неделя 4: Тестирование и Деплой
- [ ] Интеграционные тесты
- [ ] Нагрузочное тестирование (локально)
- [ ] Миграция данных на Railway
- [ ] Деплой v3.0
- [ ] Мониторинг первые 48 часов

### Неделя 5-6: Новые фичи (v3.5)
- [ ] Система ролей и permissions
- [ ] Кэширование через Redis
- [ ] Мультивалютная экономика
- [ ] Анти-абьюз система

### Неделя 7-9: Игры (v4.0)
- [ ] PvP система
- [ ] Matchmaking
- [ ] Турниры
- [ ] Сезоны и рейтинги

### Неделя 10-12: Автоматизация (v5.0)
- [ ] Job scheduler
- [ ] AI-интеграция
- [ ] Веб-панель (FastAPI)
- [ ] Аналитика и дашборды

---

## 💰 ОЦЕНКА РЕСУРСОВ

### Инфраструктура (Railway)

**v3.0 (PostgreSQL + Redis):**
- PostgreSQL: $5/месяц (Hobby план)
- Redis: $5/месяц (Hobby план)
- Bot instance: $5/месяц
- **Итого:** ~$15/месяц

**v5.0 (с AI и веб-панелью):**
- PostgreSQL: $10/месяц (Pro план)
- Redis: $10/месяц (Pro план)
- Bot instance: $10/месяц
- Web API instance: $10/месяц
- OpenAI API: ~$20/месяц (при 1000 запросов/день)
- **Итого:** ~$60/месяц

### Разработка

**Время разработки:**
- v3.0 (рефакторинг): 4 недели
- v3.5 (роли + кэш): 2 недели
- v4.0 (игры): 3 недели
- v5.0 (AI + автоматизация): 3 недели
- **Итого:** ~12 недель (3 месяца)

**Команда:**
- 1 Senior Python Developer (full-time)
- 1 DevOps Engineer (part-time)
- 1 QA Engineer (part-time)

---

## 📚 ТЕХНОЛОГИЧЕСКИЙ СТЕК

### Backend
- **Python 3.11+**
- **python-telegram-bot 20.7** (Telegram API)
- **asyncpg** (PostgreSQL async driver)
- **redis-py** (Redis client)
- **SQLAlchemy 2.0** (ORM, опционально)
- **Alembic** (миграции БД)
- **APScheduler** (job scheduler)
- **FastAPI** (веб-панель)
- **Pydantic** (валидация данных)

### Инфраструктура
- **PostgreSQL 15** (основная БД)
- **Redis 7** (кэш + очереди)
- **Railway** (хостинг)
- **Docker** (контейнеризация)
- **Prometheus + Grafana** (мониторинг)

### AI/ML
- **OpenAI GPT-4o-mini** (AI-помощник)
- **LangChain** (опционально, для сложных цепочек)

### Тестирование
- **pytest** (unit + integration тесты)
- **pytest-asyncio** (async тесты)
- **locust** (нагрузочное тестирование)

---

## 🎓 ОБУЧЕНИЕ КОМАНДЫ

### Необходимые знания

1. **Clean Architecture & DDD**
   - Разделение на слои
   - Domain-driven design
   - Repository pattern

2. **Async Python**
   - asyncio
   - async/await
   - Конкурентность

3. **PostgreSQL**
   - Транзакции
   - Индексы
   - Оптимизация запросов

4. **Redis**
   - Кэширование
   - Pub/Sub
   - Rate limiting

5. **Тестирование**
   - Unit тесты
   - Integration тесты
   - Mocking

### Рекомендуемые ресурсы
- "Clean Architecture" by Robert Martin
- "Domain-Driven Design" by Eric Evans
- "Designing Data-Intensive Applications" by Martin Kleppmann
- FastAPI documentation
- python-telegram-bot documentation

---

## ✅ ЧЕКЛИСТ ГОТОВНОСТИ К СТАРТУ

### Перед началом рефакторинга:
- [ ] Сделать полный бэкап текущей БД (JSON)
- [ ] Создать ветку `feature/v3.0-refactoring`
- [ ] Настроить локальное окружение (PostgreSQL + Redis)
- [ ] Написать миграцию данных
- [ ] Создать тестовое окружение на Railway
- [ ] Договориться о downtime (если нужен)

### Критерии успеха v3.0:
- [ ] Все текущие фичи работают
- [ ] Время ответа < 500ms (95 перцентиль)
- [ ] Нет потери данных при миграции
- [ ] Покрытие тестами > 70%
- [ ] Документация обновлена
- [ ] Команда обучена новой архитектуре

---

## 🎯 ЗАКЛЮЧЕНИЕ

Этот roadmap превращает базовый Telegram-бот в **enterprise-grade платформу** с:

✅ Масштабируемой архитектурой (Clean Architecture + DDD)  
✅ Надёжным хранилищем (PostgreSQL + Redis)  
✅ Гибкой системой прав (роли + permissions)  
✅ Глубокой экономикой (мультивалюта + анти-абьюз)  
✅ Продвинутыми играми (PvP + турниры + сезоны)  
✅ AI-интеграцией (помощь саппорту + аналитика)  
✅ Автоматизацией (фоновые задачи + мониторинг)  
✅ Готовностью к веб-панели (FastAPI)

**Следующий шаг:** Начать с Этапа 1 (Архитектурный рефакторинг) и двигаться итеративно.

Готов приступить к реализации? 🚀
