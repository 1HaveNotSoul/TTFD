-- ============================================================================
-- Миграция 005: Discord интеграция
-- ============================================================================

-- Таблица привязок Telegram ↔ Discord
CREATE TABLE IF NOT EXISTS discord_links (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    discord_user_id BIGINT,
    
    -- Код подтверждения
    verification_code VARCHAR(6) NOT NULL,
    
    -- Статус
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    -- Уникальность: один Telegram пользователь - одна активная привязка
    UNIQUE(telegram_user_id, status) WHERE status = 'active',
    
    -- Уникальность: один Discord пользователь - одна активная привязка
    UNIQUE(discord_user_id) WHERE discord_user_id IS NOT NULL AND status = 'active'
);

-- Таблица выдачи Discord ролей
CREATE TABLE IF NOT EXISTS discord_role_grants (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    
    -- Роль
    role_name VARCHAR(100) NOT NULL,
    role_id VARCHAR(50),
    
    -- Причина выдачи
    reason_type VARCHAR(50) NOT NULL,
    reason_id VARCHAR(100),
    
    -- Статус
    is_granted BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at TIMESTAMP,
    
    -- Ошибки
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Уникальность: одна роль по одной причине
    UNIQUE(telegram_user_id, role_name, reason_type, reason_id)
);

-- Таблица логов синхронизации
CREATE TABLE IF NOT EXISTS discord_sync_logs (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    
    -- Действие
    action VARCHAR(50) NOT NULL,
    
    -- Детали
    details JSONB,
    
    -- Результат
    success BOOLEAN NOT NULL,
    error_message TEXT,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_discord_links_telegram_user ON discord_links(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_discord_links_discord_user ON discord_links(discord_user_id);
CREATE INDEX IF NOT EXISTS idx_discord_links_status ON discord_links(status);
CREATE INDEX IF NOT EXISTS idx_discord_links_code ON discord_links(verification_code);

CREATE INDEX IF NOT EXISTS idx_discord_role_grants_telegram_user ON discord_role_grants(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_discord_role_grants_discord_user ON discord_role_grants(discord_user_id);
CREATE INDEX IF NOT EXISTS idx_discord_role_grants_granted ON discord_role_grants(is_granted);

CREATE INDEX IF NOT EXISTS idx_discord_sync_logs_telegram_user ON discord_sync_logs(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_discord_sync_logs_action ON discord_sync_logs(action);

-- Автоматическое обновление updated_at
CREATE OR REPLACE FUNCTION update_discord_role_grants_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_discord_role_grants_updated_at
    BEFORE UPDATE ON discord_role_grants
    FOR EACH ROW
    EXECUTE FUNCTION update_discord_role_grants_updated_at();

-- Автоматическое истечение кодов
CREATE OR REPLACE FUNCTION expire_old_verification_codes()
RETURNS void AS $$
BEGIN
    UPDATE discord_links
    SET status = 'expired'
    WHERE status = 'pending'
        AND expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Готово!
-- ============================================================================

SELECT 'Миграция 005: Discord интеграция применена успешно!' AS status;
