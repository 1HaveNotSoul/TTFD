-- ============================================================================
-- Миграция 004: Система достижений
-- ============================================================================

-- Таблица достижений
CREATE TABLE IF NOT EXISTS achievements (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(20) NOT NULL,
    rarity VARCHAR(20) NOT NULL,
    
    -- Условия получения
    requirement_type VARCHAR(50) NOT NULL,
    requirement_value INTEGER NOT NULL,
    
    -- Награды
    reward_xp INTEGER NOT NULL DEFAULT 0,
    reward_coins INTEGER NOT NULL DEFAULT 0,
    reward_discord_role VARCHAR(50),
    
    -- Иконка
    icon VARCHAR(10) NOT NULL,
    
    -- Метаданные
    is_hidden BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Таблица прогресса пользователей по достижениям
CREATE TABLE IF NOT EXISTS user_achievements (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(50) NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    
    -- Прогресс
    current_progress INTEGER NOT NULL DEFAULT 0,
    required_progress INTEGER NOT NULL,
    
    -- Статус
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    
    -- Награды
    rewards_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Уникальность: один пользователь - одно достижение
    UNIQUE(user_id, achievement_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_completed ON user_achievements(is_completed);
CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category);
CREATE INDEX IF NOT EXISTS idx_achievements_rarity ON achievements(rarity);

-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_user_achievements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_achievements_updated_at
    BEFORE UPDATE ON user_achievements
    FOR EACH ROW
    EXECUTE FUNCTION update_user_achievements_updated_at();

-- ============================================================================
-- Вставка достижений по умолчанию
-- ============================================================================

-- ИГРЫ
INSERT INTO achievements (id, name, description, category, rarity, requirement_type, requirement_value, reward_xp, reward_coins, icon, is_hidden)
VALUES 
    ('first_win', 'Первая победа', 'Выиграй свою первую игру', 'games', 'common', 'games_won', 1, 100, 50, '🎯', FALSE),
    ('winner_10', 'Везунчик', 'Выиграй 10 игр', 'games', 'common', 'games_won', 10, 200, 100, '🎲', FALSE),
    ('winner_50', 'Профессионал', 'Выиграй 50 игр', 'games', 'rare', 'games_won', 50, 500, 300, '🏅', FALSE),
    ('winner_100', 'Мастер игр', 'Выиграй 100 игр', 'games', 'epic', 'games_won', 100, 1000, 500, '🏆', FALSE),
    ('winner_500', 'Легенда', 'Выиграй 500 игр', 'games', 'legendary', 'games_won', 500, 5000, 2000, '👑', FALSE)
ON CONFLICT (id) DO NOTHING;

-- АКТИВНОСТЬ
INSERT INTO achievements (id, name, description, category, rarity, requirement_type, requirement_value, reward_xp, reward_coins, icon, is_hidden)
VALUES 
    ('active_player', 'Активный игрок', 'Сыграй 100 игр', 'activity', 'common', 'games_played', 100, 300, 150, '⚡', FALSE),
    ('dedicated_player', 'Преданный игрок', 'Сыграй 500 игр', 'activity', 'rare', 'games_played', 500, 1000, 500, '💪', FALSE),
    ('rich_player', 'Богач', 'Накопи 10000 монет', 'activity', 'rare', 'total_coins', 10000, 500, 1000, '💰', FALSE),
    ('experienced', 'Опытный', 'Достигни 10000 XP', 'activity', 'rare', 'total_xp', 10000, 1000, 500, '⭐', FALSE)
ON CONFLICT (id) DO NOTHING;

-- СТРИКИ
INSERT INTO achievements (id, name, description, category, rarity, requirement_type, requirement_value, reward_xp, reward_coins, icon, is_hidden)
VALUES 
    ('streak_3', 'Постоянство', 'Играй 3 дня подряд', 'streak', 'common', 'streak_days', 3, 150, 75, '🔥', FALSE),
    ('streak_7', 'Неделя силы', 'Играй 7 дней подряд', 'streak', 'rare', 'streak_days', 7, 500, 250, '🔥🔥', FALSE),
    ('streak_30', 'Месяц преданности', 'Играй 30 дней подряд', 'streak', 'epic', 'streak_days', 30, 2000, 1000, '🔥🔥🔥', FALSE)
ON CONFLICT (id) DO NOTHING;

-- ТИКЕТЫ
INSERT INTO achievements (id, name, description, category, rarity, requirement_type, requirement_value, reward_xp, reward_coins, icon, is_hidden)
VALUES 
    ('first_ticket', 'Первое обращение', 'Создай свой первый тикет', 'tickets', 'common', 'tickets_created', 1, 50, 25, '🎫', FALSE),
    ('helpful_user', 'Полезный пользователь', 'Получи 5 решённых тикетов', 'tickets', 'rare', 'tickets_resolved', 5, 300, 150, '✅', FALSE)
ON CONFLICT (id) DO NOTHING;

-- СЕЗОНЫ
INSERT INTO achievements (id, name, description, category, rarity, requirement_type, requirement_value, reward_xp, reward_coins, icon, is_hidden)
VALUES 
    ('season_participant', 'Участник сезона', 'Сыграй хотя бы одну игру в сезоне', 'season', 'common', 'season_games', 1, 100, 50, '🎮', FALSE),
    ('season_top50', 'Топ-50 сезона', 'Попади в топ-50 сезона', 'season', 'rare', 'season_rank', 50, 500, 250, '🌟', FALSE),
    ('season_top10', 'Топ-10 сезона', 'Попади в топ-10 сезона', 'season', 'epic', 'season_rank', 10, 1500, 750, '💎', FALSE),
    ('season_champion', 'Чемпион сезона', 'Стань первым в сезоне', 'season', 'legendary', 'season_rank', 1, 5000, 2500, '👑', FALSE)
ON CONFLICT (id) DO NOTHING;

-- СПЕЦИАЛЬНЫЕ (скрытые)
INSERT INTO achievements (id, name, description, category, rarity, requirement_type, requirement_value, reward_xp, reward_coins, icon, is_hidden)
VALUES 
    ('lucky_spin', 'Удача улыбнулась', 'Выиграй джекпот в спине', 'special', 'epic', 'spin_jackpot', 1, 1000, 500, '🎰', TRUE),
    ('perfect_quiz', 'Эрудит', 'Ответь правильно на 10 квизов подряд', 'special', 'epic', 'quiz_streak', 10, 1500, 750, '🧠', TRUE)
ON CONFLICT (id) DO NOTHING;

-- Добавляем Discord роли для некоторых достижений
UPDATE achievements SET reward_discord_role = 'achievement_pro' WHERE id = 'winner_50';
UPDATE achievements SET reward_discord_role = 'achievement_master' WHERE id = 'winner_100';
UPDATE achievements SET reward_discord_role = 'achievement_legend' WHERE id = 'winner_500';
UPDATE achievements SET reward_discord_role = 'achievement_dedicated' WHERE id = 'dedicated_player';
UPDATE achievements SET reward_discord_role = 'achievement_streak7' WHERE id = 'streak_7';
UPDATE achievements SET reward_discord_role = 'achievement_streak30' WHERE id = 'streak_30';
UPDATE achievements SET reward_discord_role = 'achievement_season_top10' WHERE id = 'season_top10';
UPDATE achievements SET reward_discord_role = 'achievement_season_champion' WHERE id = 'season_champion';
UPDATE achievements SET reward_discord_role = 'achievement_erudite' WHERE id = 'perfect_quiz';

-- ============================================================================
-- Готово!
-- ============================================================================

SELECT 'Миграция 004: Система достижений применена успешно!' AS status;
SELECT COUNT(*) AS total_achievements FROM achievements;
