-- Обновление таблицы game_history для v3.0

-- Удаляем старую таблицу если есть
DROP TABLE IF EXISTS game_history CASCADE;

-- Создаём новую с правильной структурой
CREATE TABLE game_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL,
    bet_amount INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress',
    result JSONB,
    reward_coins INTEGER DEFAULT 0,
    reward_xp INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Индексы
CREATE INDEX idx_game_history_user_id ON game_history(user_id);
CREATE INDEX idx_game_history_game_type ON game_history(game_type);
CREATE INDEX idx_game_history_status ON game_history(status);
CREATE INDEX idx_game_history_created_at ON game_history(created_at DESC);

COMMENT ON TABLE game_history IS 'История игр пользователей';
COMMENT ON COLUMN game_history.status IS 'Статус: in_progress, won, lost, cancelled';
COMMENT ON COLUMN game_history.result IS 'JSON с деталями результата игры';
