# 🏗️ Architecture - TTFD Project

Архитектура и взаимодействие компонентов экосистемы TTFD.

## 📊 Общая схема

```
┌─────────────────────────────────────────────────────────────┐
│                         TTFD Ecosystem                       │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
        ┌───────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
        │   Website    │ │Discord │ │  Cleaner   │
        │   (Flask)    │ │  Bot   │ │ (Desktop)  │
        └──────┬───────┘ └───┬────┘ └────────────┘
               │             │
               └──────┬──────┘
                      │
              ┌───────▼────────┐
              │   PostgreSQL   │
              │    Database    │
              └────────────────┘
```

## 🌐 Website (Flask)

### Технологии
- **Framework:** Flask 3.0+
- **Template Engine:** Jinja2
- **Database:** PostgreSQL (через psycopg2)
- **Auth:** Discord OAuth 2.0
- **Deployment:** Render.com (Web Service)

### Структура

```
website/
├── app.py                 # Flask приложение и роуты
├── main.py                # Точка входа
├── config.py              # Конфигурация
├── discord_oauth.py       # Discord OAuth логика
├── database.py            # Database wrapper (JSON)
├── database_postgres.py   # Database wrapper (PostgreSQL)
├── static/
│   ├── css/               # Стили
│   ├── js/                # JavaScript
│   └── фотографии/        # Изображения
└── templates/             # HTML шаблоны
    ├── base.html          # Базовый шаблон
    ├── index.html         # Главная
    ├── login.html         # Вход
    ├── profile.html       # Профиль
    ├── settings.html      # Настройки
    ├── customize.html     # Кастомизация
    └── shop.html          # Магазин
```

### Роуты

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Главная страница |
| `/login` | GET | Страница входа |
| `/auth/discord` | GET | Redirect на Discord OAuth |
| `/auth/discord/callback` | GET | Callback после OAuth |
| `/profile` | GET | Профиль пользователя |
| `/profile/<user_id>` | GET | Профиль другого пользователя |
| `/settings` | GET, POST | Настройки аккаунта |
| `/customize` | GET, POST | Кастомизация профиля |
| `/shop` | GET | Магазин |
| `/logout` | GET | Выход |

### Database Schema (PostgreSQL)

```sql
CREATE TABLE users (
    discord_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    discriminator VARCHAR(4),
    avatar VARCHAR(100),
    email VARCHAR(255),
    coins INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    rank VARCHAR(50) DEFAULT 'Новичок',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    
    -- Кастомизация
    theme VARCHAR(20) DEFAULT 'dark',
    primary_color VARCHAR(7) DEFAULT '#7289da',
    background_image VARCHAR(255),
    music_url VARCHAR(500),
    bio TEXT,
    
    -- Настройки
    show_email BOOLEAN DEFAULT FALSE,
    show_stats BOOLEAN DEFAULT TRUE,
    notifications BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_level ON users(level DESC);
```

### Функции

**Авторизация:**
- `get_current_user()` - Получить текущего пользователя из сессии
- `login_required()` - Декоратор для защищённых роутов

**Database:**
- `get_user(discord_id)` - Получить пользователя
- `create_user(data)` - Создать пользователя
- `update_user(discord_id, data)` - Обновить пользователя

## 🤖 Discord Bot

### Технологии
- **Library:** discord.py 2.3+
- **Database:** PostgreSQL (через psycopg2)
- **Deployment:** Render.com (Background Worker)

### Структура

```
discord-bot/
├── main.py                # Точка входа
├── py/
│   ├── bot.py             # Основной файл бота
│   ├── commands_manager.py    # Менеджер команд
│   ├── font_converter.py      # Конвертер шрифта
│   ├── verification_system.py # Верификация
│   ├── tickets_system.py      # Тикеты
│   ├── shop_system.py         # Магазин
│   ├── rank_system.py         # Система рангов
│   └── database.py            # Database wrapper
├── md/                    # Документация
├── json/                  # JSON данные
└── фотографии/            # Изображения
```

### Команды

**Основные:**
- `!ping` - Проверка работы бота
- `!stats` - Статистика сервера
- `!link` - Ссылка на сайт

**Профиль:**
- `!profile [@user]` - Профиль пользователя
- `!rank [@user]` - Ранг пользователя
- `!daily` - Ежедневная награда
- `!leaderboard` - Таблица лидеров

**Мини-игры:**
- `!dice` - Бросок кубика
- `!coinflip` - Монетка
- `!rps` - Камень-ножницы-бумага

**Поддержка:**
- `!ticket` - Создать тикет
- `!close` - Закрыть тикет

**Модерация:**
- `!clear <amount>` - Очистить сообщения
- `!kick <user>` - Кикнуть пользователя
- `!ban <user>` - Забанить пользователя

**Администрирование:**
- `!update <text>` - Отправить обновление
- `!updatecommands` - Обновить список команд
- `!setupverification` - Настроить верификацию

### Events

```python
@bot.event
async def on_ready():
    # Бот подключился
    
@bot.event
async def on_message(message):
    # Новое сообщение (XP система)
    
@bot.event
async def on_member_join(member):
    # Новый участник
    
@bot.event
async def on_member_remove(member):
    # Участник покинул сервер
```

### Database Schema (PostgreSQL)

```sql
CREATE TABLE discord_users (
    discord_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    discriminator VARCHAR(4),
    coins INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    rank VARCHAR(50) DEFAULT 'Новичок',
    daily_streak INTEGER DEFAULT 0,
    last_daily TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    voice_time INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    channel_id VARCHAR(20) UNIQUE NOT NULL,
    user_id VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES discord_users(discord_id)
);

CREATE TABLE shop_items (
    item_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    category VARCHAR(50),
    stock INTEGER DEFAULT -1,
    image_url VARCHAR(255)
);

CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    total_price INTEGER NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES discord_users(discord_id),
    FOREIGN KEY (item_id) REFERENCES shop_items(item_id)
);
```

## 🧹 Cleaner (Desktop)

### Технологии
- **GUI:** Python (tkinter)
- **Backend:** C# (.NET 8)
- **Packaging:** PyInstaller
- **Distribution:** Standalone EXE

### Структура

```
cleaner/
├── main_menu.py           # Главное меню
├── gui.py                 # Старый GUI
├── gui_autoruns_style.py  # Autoruns интерфейс
├── sections/              # Разделы меню
│   ├── cleaning_window.py
│   ├── reports_window.py
│   ├── startup_window.py
│   ├── browsers_window.py
│   ├── apps_window.py
│   └── exclusions_window.py
├── assets/                # Ассеты меню
├── Backend/               # C# Backend
│   ├── Commands/
│   ├── Models/
│   └── Utils/
└── TTFD.Cleaner.Cli.exe   # CLI бэкенд
```

### Архитектура

```
┌─────────────────────────────────────┐
│      Python GUI (tkinter)           │
│  ┌─────────────────────────────┐   │
│  │   Main Menu (main_menu.py)  │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│  ┌──────────▼──────────────────┐   │
│  │  Section Windows (sections/) │   │
│  └──────────┬──────────────────┘   │
└─────────────┼───────────────────────┘
              │ subprocess.run()
              │
┌─────────────▼───────────────────────┐
│   C# CLI Backend (.NET 8)           │
│  ┌─────────────────────────────┐   │
│  │  TTFD.Cleaner.Cli.exe       │   │
│  │  ├── scan-cleaning          │   │
│  │  ├── apply-cleaning         │   │
│  │  ├── scan-startup           │   │
│  │  ├── toggle-startup         │   │
│  │  └── status                 │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### CLI Commands

```bash
# Статус системы
TTFD.Cleaner.Cli.exe status

# Сканирование очистки
TTFD.Cleaner.Cli.exe scan-cleaning --categories temp,cache

# Применение очистки
TTFD.Cleaner.Cli.exe apply-cleaning --categories temp --yes

# Сканирование автозапуска
TTFD.Cleaner.Cli.exe scan-startup --category logon

# Переключение автозапуска
TTFD.Cleaner.Cli.exe toggle-startup --id "entry_id" --enable
```

## 🔄 Взаимодействие компонентов

### Website ↔ Discord Bot

**Синхронизация данных:**

```python
# Website: получить данные из Discord
def sync_discord_data(discord_id):
    user = db.get_user(discord_id)
    # Данные уже синхронизированы через общую БД
    return user

# Discord Bot: обновить данные
async def update_user_xp(user_id, xp):
    db.update_user(user_id, {'xp': xp})
    # Автоматически доступно на сайте
```

**Общая база данных:**
- Оба используют одну PostgreSQL базу
- Синхронизация в реальном времени
- Единая схема данных

### Website → Cleaner

**Будущая интеграция (v2.0):**

```python
# API endpoint для статистики
@app.route('/api/cleaner/stats')
def cleaner_stats():
    # Получить статистику от пользователей
    # Агрегировать данные
    return jsonify(stats)
```

### Discord Bot → Cleaner

**Будущая интеграция (v2.0):**

```python
# Команда для получения статистики
@bot.command()
async def cleanerstats(ctx):
    # Получить статистику через API
    stats = await fetch_cleaner_stats()
    await ctx.send(embed=create_stats_embed(stats))
```

## 🗄️ Database Design

### Общие таблицы

```sql
-- Пользователи (используется Website и Discord Bot)
CREATE TABLE users (
    discord_id VARCHAR(20) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    -- Website поля
    email VARCHAR(255),
    theme VARCHAR(20),
    -- Discord Bot поля
    coins INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    -- Общие поля
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Разделение данных

**Website-specific:**
- Кастомизация профиля
- Настройки приватности
- Email

**Discord Bot-specific:**
- Тикеты
- Покупки в магазине
- Голосовое время

**Shared:**
- Базовая информация
- Монеты и XP
- Ранг и уровень

## 🔐 Security

### Authentication Flow

```
User → Discord OAuth → Discord API
                          ↓
                    Authorization Code
                          ↓
Website → Exchange Code → Access Token
                          ↓
                    User Information
                          ↓
                    Create/Update User
                          ↓
                    Session Cookie
```

### Environment Variables

```env
# Критичные секреты
DISCORD_TOKEN=***           # Discord Bot Token
DISCORD_CLIENT_SECRET=***   # OAuth Secret
SECRET_KEY=***              # Flask Secret
DATABASE_URL=***            # Database URL

# Публичные данные
DISCORD_CLIENT_ID=***       # OAuth Client ID
GUILD_ID=***                # Discord Server ID
PORT=10000                  # Website Port
```

## 📈 Scalability

### Current (Free Tier)

```
Website:     1 instance, 512 MB RAM
Discord Bot: 1 instance, 512 MB RAM
Database:    Free tier, 1 GB storage
```

### Future (Paid Tier)

```
Website:     Multiple instances, Load Balancer
Discord Bot: Sharding (multiple shards)
Database:    Dedicated instance, Replication
Cache:       Redis for sessions
CDN:         Static assets
```

## 🚀 Performance

### Website

- **Response Time:** < 200ms
- **Concurrent Users:** ~100 (Free tier)
- **Database Queries:** Optimized with indexes

### Discord Bot

- **Command Response:** < 1s
- **Message Processing:** < 100ms
- **Concurrent Commands:** ~50

### Cleaner

- **Scan Time:** 5-30s (зависит от системы)
- **Memory Usage:** ~100 MB
- **CPU Usage:** Low (background)

## 📊 Monitoring

### Metrics

```python
# Website
- Request count
- Response time
- Error rate
- Active users

# Discord Bot
- Commands executed
- Messages processed
- Active users
- Uptime

# Database
- Query time
- Connection pool
- Storage usage
```

### Logging

```python
# Structured logging
logger.info("User logged in", extra={
    "user_id": user_id,
    "ip": request.remote_addr,
    "timestamp": datetime.now()
})
```

## 🔄 CI/CD

### GitHub Actions (Future)

```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        run: |
          # Trigger Render deploy
```

---

**Version:** 2.0.0  
**Last Updated:** 05.02.2026
