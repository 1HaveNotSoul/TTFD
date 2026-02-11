-- Initial database schema for TTFD Telegram Bot v3.0

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    xp INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    rank_id INTEGER DEFAULT 1,
    role VARCHAR(20) DEFAULT 'user',
    discord_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    last_daily TIMESTAMP,
    last_spin TIMESTAMP,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_xp ON users(xp DESC);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Транзакции (история экономики)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    currency VARCHAR(20) DEFAULT 'coins',
    description TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at DESC);

-- Инвентарь
CREATE TABLE IF NOT EXISTS inventory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory(user_id);

-- История игр
CREATE TABLE IF NOT EXISTS game_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    game_type VARCHAR(50) NOT NULL,
    bet_amount INTEGER,
    win_amount INTEGER,
    result VARCHAR(20),
    details JSONB,
    played_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_history_user_id ON game_history(user_id);
CREATE INDEX IF NOT EXISTS idx_game_history_game_type ON game_history(game_type);
CREATE INDEX IF NOT EXISTS idx_game_history_played_at ON game_history(played_at DESC);

-- Тикеты
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'open',
    subject TEXT NOT NULL,
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    closed_at TIMESTAMP,
    sla_deadline TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tickets_user_id ON tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned_to ON tickets(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at DESC);

-- Сообщения тикетов
CREATE TABLE IF NOT EXISTS ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ticket_messages_ticket_id ON ticket_messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_messages_created_at ON ticket_messages(created_at);

-- Достижения
CREATE TABLE IF NOT EXISTS achievements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    reward_xp INTEGER DEFAULT 0,
    reward_coins INTEGER DEFAULT 0,
    icon VARCHAR(50)
);

-- Достижения пользователей
CREATE TABLE IF NOT EXISTS user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    achievement_id INTEGER REFERENCES achievements(id) ON DELETE CASCADE,
    unlocked_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements(user_id);

-- Глобальная статистика
CREATE TABLE IF NOT EXISTS global_stats (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) UNIQUE NOT NULL,
    value BIGINT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Инициализация глобальной статистики
INSERT INTO global_stats (key, value) VALUES
    ('total_users', 0),
    ('total_xp_earned', 0),
    ('total_coins_earned', 0),
    ('total_games_played', 0)
ON CONFLICT (key) DO NOTHING;

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для tickets
CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE users IS 'Пользователи бота';
COMMENT ON TABLE transactions IS 'История транзакций';
COMMENT ON TABLE inventory IS 'Инвентарь пользователей';
COMMENT ON TABLE game_history IS 'История игр';
COMMENT ON TABLE tickets IS 'Тикеты поддержки';
COMMENT ON TABLE ticket_messages IS 'Сообщения в тикетах';
COMMENT ON TABLE achievements IS 'Достижения';
COMMENT ON TABLE user_achievements IS 'Достижения пользователей';
COMMENT ON TABLE global_stats IS 'Глобальная статистика';
