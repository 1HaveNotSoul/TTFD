-- Миграция 003: Система сезонов
-- Добавляет таблицы для сезонов и прогресса пользователей

-- Таблица сезонов
CREATE TABLE IF NOT EXISTS seasons (
    id SERIAL PRIMARY KEY,
    number INTEGER NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'upcoming',
    rewards_config JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_status CHECK (status IN ('active', 'ended', 'upcoming')),
    CONSTRAINT check_dates CHECK (end_date > start_date)
);

-- Индексы для сезонов
CREATE INDEX IF NOT EXISTS idx_seasons_status ON seasons(status);
CREATE INDEX IF NOT EXISTS idx_seasons_dates ON seasons(start_date, end_date);

-- Таблица прогресса пользователей в сезонах
CREATE TABLE IF NOT EXISTS season_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    season_id INTEGER NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
    
    -- Сезонная статистика
    season_xp INTEGER NOT NULL DEFAULT 0,
    season_coins INTEGER NOT NULL DEFAULT 0,
    games_played INTEGER NOT NULL DEFAULT 0,
    games_won INTEGER NOT NULL DEFAULT 0,
    
    -- Стрики
    current_streak INTEGER NOT NULL DEFAULT 0,
    best_streak INTEGER NOT NULL DEFAULT 0,
    last_activity_date TIMESTAMP,
    
    -- Рейтинг
    rank INTEGER,
    
    -- Награды
    rewards_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, season_id)
);

-- Индексы для прогресса
CREATE INDEX IF NOT EXISTS idx_season_progress_user ON season_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_season_progress_season ON season_progress(season_id);
CREATE INDEX IF NOT EXISTS idx_season_progress_xp ON season_progress(season_id, season_xp DESC);
CREATE INDEX IF NOT EXISTS idx_season_progress_rank ON season_progress(season_id, rank);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_season_progress_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления updated_at
DROP TRIGGER IF EXISTS trigger_update_season_progress_updated_at ON season_progress;
CREATE TRIGGER trigger_update_season_progress_updated_at
    BEFORE UPDATE ON season_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_season_progress_updated_at();

-- Создаём первый сезон (30 дней от текущей даты)
INSERT INTO seasons (number, name, start_date, end_date, status, rewards_config)
VALUES (
    1,
    'Сезон 1: Начало',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP + INTERVAL '30 days',
    'active',
    '[
        {"rank_from": 1, "rank_to": 1, "xp": 5000, "coins": 1000, "discord_role": "season_champion", "title": "🏆 Чемпион сезона"},
        {"rank_from": 2, "rank_to": 3, "xp": 3000, "coins": 500, "discord_role": "season_top3", "title": "🥈 Топ-3 сезона"},
        {"rank_from": 4, "rank_to": 10, "xp": 2000, "coins": 300, "discord_role": "season_top10", "title": "🥉 Топ-10 сезона"},
        {"rank_from": 11, "rank_to": 50, "xp": 1000, "coins": 150, "discord_role": null, "title": "⭐ Топ-50 сезона"}
    ]'::jsonb
)
ON CONFLICT (number) DO NOTHING;

-- Комментарии
COMMENT ON TABLE seasons IS 'Игровые сезоны (30 дней)';
COMMENT ON TABLE season_progress IS 'Прогресс пользователей в сезонах';
COMMENT ON COLUMN season_progress.season_xp IS 'XP заработанный в этом сезоне';
COMMENT ON COLUMN season_progress.current_streak IS 'Текущий стрик активности (дни подряд)';
COMMENT ON COLUMN season_progress.rank IS 'Позиция в сезонном рейтинге';
