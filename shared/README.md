# 🔗 TTFD Shared Module

**Единая база данных для всех платформ TTFD**

---

## 📦 Содержимое

```
shared/
├── models.py                # Единые модели данных
├── database_unified.py      # Unified Database класс
├── migration_unified.sql    # SQL миграция
├── migrate_to_unified.py    # Скрипт миграции данных
├── sync_worker.py           # Воркер синхронизации
└── README.md                # Этот файл
```

---

## 🚀 Быстрый старт

### 1. Применить миграцию

```bash
psql $DATABASE_URL -f migration_unified.sql
```

### 2. Мигрировать данные

```bash
python migrate_to_unified.py
```

### 3. Использовать в коде

```python
import sys
sys.path.append('path/to/shared')

from database_unified import get_unified_db

async def example():
    db = await get_unified_db()
    
    # Получить пользователя
    user = await db.get_user_by_telegram('123456789')
    
    # Обновить XP
    result = await db.update_xp(user.id, delta_xp=50)
    
    # Создать событие
    await db.create_event(
        user_id=user.id,
        event_type='xp_change',
        source_platform='telegram',
        data={'delta_xp': 50}
    )
    
    await db.disconnect()
```

---

## 📊 Модели

### UnifiedUser

```python
@dataclass
class UnifiedUser:
    id: int                          # Внутренний ID
    telegram_id: Optional[str]       # Telegram ID
    discord_id: Optional[str]        # Discord ID
    website_email: Optional[str]     # Website email
    username: str                    # Username
    display_name: str                # Отображаемое имя
    xp: int                          # Опыт
    coins: int                       # Монеты
    rank_id: int                     # ID ранга
    games_played: int                # Игр сыграно
    games_won: int                   # Игр выиграно
    total_voice_time: int            # Время в войсе (сек)
    messages_sent: int               # Сообщений отправлено
    achievements: List[str]          # Достижения
    current_season_xp: int           # XP текущего сезона
    season_rank: int                 # Ранг в сезоне
    daily_streak: int                # Серия ежедневных входов
    created_at: datetime             # Дата создания
    last_active: datetime            # Последняя активность
    last_daily: Optional[datetime]   # Последний ежедневный вход
    platforms: List[str]             # Привязанные платформы
    primary_platform: str            # Основная платформа
```

### Rank

```python
@dataclass
class Rank:
    id: int                # ID ранга (1-20)
    name: str              # Название ("Ранг F I")
    tier: str              # Tier (F, E, D, C, B, A, S)
    stars: int             # Звёзды (1, 2, 3)
    color: str             # Цвет (hex)
    required_xp: int       # Требуемый XP
    reward_coins: int      # Награда монетами
    emoji: Optional[str]   # Эмодзи Discord
```

### CrossPlatformEvent

```python
@dataclass
class CrossPlatformEvent:
    id: str                    # UUID
    user_id: int               # ID пользователя
    event_type: str            # Тип события
    source_platform: str       # Источник
    data: Dict[str, Any]       # Данные
    processed: bool            # Обработано?
    processed_at: Optional[datetime]
    created_at: datetime
```

---

## 🔧 API

### UnifiedDatabase

#### Подключение

```python
db = await get_unified_db()
await db.disconnect()
```

#### Пользователи

```python
# Получить по платформе
user = await db.get_user_by_telegram('123456789')
user = await db.get_user_by_discord('987654321')
user = await db.get_user_by_website('user@example.com')

# Получить по ID
user = await db.get_user_by_id(1)

# Создать
user = await db.create_user(
    telegram_id='123456789',
    username='testuser',
    display_name='Test User',
    primary_platform='telegram'
)

# Привязать платформу
success = await db.link_telegram(user_id, telegram_id)
success = await db.link_discord(user_id, discord_id)
success = await db.link_website(user_id, email)
```

#### XP и монеты

```python
# Обновить XP
result = await db.update_xp(user_id, delta_xp=50)
# result = {
#     'success': True,
#     'xp': 550,
#     'rank_up': True,
#     'old_rank': 1,
#     'new_rank': 2,
#     'reward_coins': 50
# }

# Обновить монеты
new_coins = await db.update_coins(user_id, delta_coins=100)
```

#### Таблица лидеров

```python
users = await db.get_leaderboard(limit=10)
for user in users:
    print(f"{user.display_name}: {user.xp} XP")
```

#### События

```python
# Создать событие
event_id = await db.create_event(
    user_id=user.id,
    event_type='xp_change',
    source_platform='telegram',
    data={'delta_xp': 50, 'new_xp': 550}
)

# Получить необработанные
events = await db.get_pending_events(limit=100)

# Отметить обработанным
await db.mark_event_processed(event_id)
```

---

## 🔄 Sync Worker

### Запуск

```python
from sync_worker import get_sync_worker, stop_sync_worker

# Запустить
worker = await get_sync_worker()

# Остановить
await stop_sync_worker()
```

### Типы событий

- `xp_change` - изменение XP
- `coins_change` - изменение монет
- `rank_up` - повышение ранга
- `achievement_unlock` - разблокировка достижения
- `game_played` - сыгранная игра
- `voice_time` - время в войсе
- `message_sent` - отправленное сообщение

---

## 📝 Примеры

### Telegram Bot

```python
from unified_integration import get_unified_integration

unified = await get_unified_integration()

# Получить или создать пользователя
user = await unified.get_or_create_user(
    telegram_id=str(update.effective_user.id),
    username=update.effective_user.username,
    display_name=update.effective_user.first_name
)

# Обновить XP
result = await unified.update_xp(
    telegram_id=str(update.effective_user.id),
    delta_xp=50
)

# Записать игру
await unified.record_game(
    telegram_id=str(update.effective_user.id),
    game_type='guess',
    won=True,
    xp_earned=50
)
```

### Discord Bot

```python
from unified_integration import get_discord_unified

unified = await get_discord_unified()

# Записать время в войсе
await unified.record_voice_time(
    discord_id=str(member.id),
    duration=300,  # 5 минут
    xp_earned=15
)

# Записать сообщение
await unified.record_message(
    discord_id=str(message.author.id),
    xp_earned=5
)
```

### Website

```python
from unified_integration import get_website_unified

unified = get_website_unified()

# Получить пользователя
user = unified.get_user_by_email('user@example.com')

# Привязать Discord
success = unified.link_discord(
    website_email='user@example.com',
    discord_id='987654321'
)

# Получить статистику
stats = unified.get_user_stats('user@example.com')
```

---

## 🗄️ База данных

### Таблицы

```sql
unified_users
├── id (PK)
├── telegram_id (unique)
├── discord_id (unique)
├── website_email (unique)
├── username, display_name
├── xp, coins, rank_id
├── games_played, games_won
├── total_voice_time, messages_sent
├── achievements (jsonb)
├── current_season_xp, season_rank
├── daily_streak, last_daily
├── created_at, last_active
└── platforms (jsonb), primary_platform

cross_platform_events
├── id (UUID, PK)
├── user_id → unified_users
├── event_type
├── source_platform
├── data (jsonb)
├── processed
├── processed_at
└── created_at
```

### Индексы

```sql
idx_unified_users_telegram    ON unified_users(telegram_id)
idx_unified_users_discord     ON unified_users(discord_id)
idx_unified_users_website     ON unified_users(website_email)
idx_unified_users_xp          ON unified_users(xp DESC)

idx_cross_platform_events_user      ON cross_platform_events(user_id)
idx_cross_platform_events_processed ON cross_platform_events(processed)
idx_cross_platform_events_created   ON cross_platform_events(created_at)
```

---

## 🔒 Безопасность

- ✅ Уникальные индексы на все ID платформ
- ✅ Foreign key constraints
- ✅ Check constraint (хотя бы одна платформа)
- ✅ Async/await для производительности
- ✅ Connection pooling

---

## 📚 Документация

- `../ИНТЕГРАЦИЯ_ПЛАТФОРМ.md` - полная архитектура
- `../СЛЕДУЮЩИЕ_ШАГИ_ИНТЕГРАЦИЯ.md` - инструкция по интеграции
- `../БЫСТРЫЙ_СТАРТ_ИНТЕГРАЦИЯ.md` - быстрый старт
- `../ФИНАЛЬНАЯ_СВОДКА_ИНТЕГРАЦИЯ.md` - финальная сводка

---

## 🐛 Troubleshooting

### "DATABASE_URL не установлен"

```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
```

### "Таблица не существует"

```bash
psql $DATABASE_URL -f migration_unified.sql
```

### "ModuleNotFoundError"

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'path', 'to', 'shared'))
```

---

## ✅ Готово!

Shared модуль готов к использованию во всех платформах TTFD.
