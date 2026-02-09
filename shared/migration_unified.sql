-- ============================================================================
-- Миграция: Unified Database для всех платформ
-- Создаёт единую таблицу пользователей для Telegram, Discord и Website
-- ============================================================================

-- Таблица унифицированных пользователей
CREATE TABLE IF NOT EXISTS unified_users (
    id SERIAL PRIMARY KEY,
    
    -- Привязки платформ (каждая уникальна)
    telegram_id TEXT UNIQUE,
    discord_id TEXT UNIQUE,
    website_email TEXT UNIQUE,
    
    -- Основная информация
    username TEXT NOT NULL DEFAULT 'Unknown',
    display_name TEXT NOT NULL DEFAULT 'Unknown',
    
    -- Игровые данные
    xp INTEGER NOT NULL DEFAULT 0,
    coins INTEGER NOT NULL DEFAULT 0,
    rank_id INTEGER NOT NULL DEFAULT 1,
    
    -- Статистика
    games_played INTEGER NOT NULL DEFAULT 0,
    games_won INTEGER NOT NULL DEFAULT 0,
    total_voice_time INTEGER NOT NULL DEFAULT 0,
    messages_sent INTEGER NOT NULL DEFAULT 0,
    
    -- Достижения и прогресс
    achievements JSONB DEFAULT '[]'::jsonb,
    current_season_xp INTEGER NOT NULL DEFAULT 0,
    season_rank INTEGER NOT NULL DEFAULT 0,
    daily_streak INTEGER NOT NULL DEFAULT 0,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_daily TIMESTAMP,
    
    -- Привязки
    platforms JSONB DEFAULT '[]'::jsonb,
    primary_platform TEXT NOT NULL DEFAULT 'telegram',
    
    -- Проверка: хотя бы одна платформа должна быть привязана
    CONSTRAINT check_at_least_one_platform CHECK (
        telegram_id IS NOT NULL OR 
        discord_id IS NOT NULL OR 
        website_email IS NOT NULL
    )
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_unified_users_telegram ON unified_users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_unified_users_discord ON unified_users(discord_id);
CREATE INDEX IF NOT EXISTS idx_unified_users_website ON unified_users(website_email);
CREATE INDEX IF NOT EXISTS idx_unified_users_xp ON unified_users(xp DESC);

-- Таблица событий синхронизации между платформами
CREATE TABLE IF NOT EXISTS cross_platform_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES unified_users(id) ON DELETE CASCADE,
    
    -- Тип и источник
    event_type TEXT NOT NULL,
    source_platform TEXT NOT NULL,
    
    -- Данные
    data JSONB NOT NULL,
    
    -- Статус
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMP,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для событий
CREATE INDEX IF NOT EXISTS idx_cross_platform_events_user ON cross_platform_events(user_id);
CREATE INDEX IF NOT EXISTS idx_cross_platform_events_processed ON cross_platform_events(processed);
CREATE INDEX IF NOT EXISTS idx_cross_platform_events_created ON cross_platform_events(created_at);

-- ============================================================================
-- Готово!
-- ============================================================================

SELECT 'Unified Database создана успешно!' AS status;
SELECT COUNT(*) AS total_users FROM unified_users;
