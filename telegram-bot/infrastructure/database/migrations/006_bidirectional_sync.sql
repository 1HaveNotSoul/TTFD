-- ============================================================================
-- Миграция 006: Двусторонняя синхронизация Telegram ↔ Discord
-- ============================================================================

-- Расширение существующей таблицы discord_links
ALTER TABLE discord_links ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP;
ALTER TABLE discord_links ADD COLUMN IF NOT EXISTS sync_enabled BOOLEAN NOT NULL DEFAULT TRUE;

-- Таблица событий синхронизации
CREATE TABLE IF NOT EXISTS sync_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    
    -- Источник и тип
    source VARCHAR(20) NOT NULL CHECK (source IN ('telegram', 'discord')),
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'xp_change', 'balance_change', 'rank_change',
        'achievement_unlock', 'reward_grant'
    )),
    
    -- Пользователь
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Данные события
    payload JSONB NOT NULL,
    
    -- Статус обработки
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'completed', 'failed'
    )),
    processed_by VARCHAR(50),  -- telegram, discord, both
    
    -- Ошибки и повторы
    retries INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    
    -- Индексы
    INDEX idx_sync_events_status (status),
    INDEX idx_sync_events_user_id (user_id),
    INDEX idx_sync_events_created_at (created_at),
    INDEX idx_sync_events_idempotency (idempotency_key)
);

-- Таблица транзакций (для аудита)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    idempotency_key VARCHAR(255) NOT NULL UNIQUE,
    
    -- Пользователь
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Источник и тип
    source VARCHAR(20) NOT NULL CHECK (source IN ('telegram', 'discord')),
    type VARCHAR(20) NOT NULL CHECK (type IN ('xp', 'balance', 'achievement', 'reward')),
    
    -- Изменения
    delta_xp INTEGER NOT NULL DEFAULT 0,
    delta_balance INTEGER NOT NULL DEFAULT 0,
    
    -- Причина
    reason TEXT NOT NULL,
    metadata JSONB,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Индексы
    INDEX idx_transactions_user_id (user_id),
    INDEX idx_transactions_created_at (created_at),
    INDEX idx_transactions_source (source)
);

-- Таблица состояния синхронизации
CREATE TABLE IF NOT EXISTS sync_state (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Последние значения Telegram
    last_telegram_xp INTEGER NOT NULL DEFAULT 0,
    last_telegram_balance INTEGER NOT NULL DEFAULT 0,
    last_telegram_rank INTEGER NOT NULL DEFAULT 1,
    
    -- Последние значения Discord
    last_discord_xp INTEGER NOT NULL DEFAULT 0,
    last_discord_balance INTEGER NOT NULL DEFAULT 0,
    last_discord_rank INTEGER NOT NULL DEFAULT 1,
    
    -- Reconcile
    last_reconcile_at TIMESTAMP,
    reconcile_errors INTEGER NOT NULL DEFAULT 0,
    
    -- Метаданные
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Таблица маппинга рангов на Discord роли
CREATE TABLE IF NOT EXISTS rank_role_mappings (
    id SERIAL PRIMARY KEY,
    
    -- Ранг (из существующей системы)
    rank_id INTEGER NOT NULL,
    rank_name VARCHAR(100) NOT NULL,
    
    -- Discord роль
    discord_role_id VARCHAR(50) NOT NULL,
    discord_role_name VARCHAR(100) NOT NULL,
    
    -- Приоритет (для сортировки)
    priority INTEGER NOT NULL DEFAULT 0,
    
    -- Активность
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Метаданные
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Уникальность
    UNIQUE(rank_id),
    UNIQUE(discord_role_id)
);

-- Автоматическое обновление updated_at для sync_state
CREATE OR REPLACE FUNCTION update_sync_state_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_sync_state_updated_at
    BEFORE UPDATE ON sync_state
    FOR EACH ROW
    EXECUTE FUNCTION update_sync_state_updated_at();

-- Автоматическое обновление updated_at для rank_role_mappings
CREATE OR REPLACE FUNCTION update_rank_role_mappings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_rank_role_mappings_updated_at
    BEFORE UPDATE ON rank_role_mappings
    FOR EACH ROW
    EXECUTE FUNCTION update_rank_role_mappings_updated_at();

-- Функция для очистки старых событий (старше 30 дней)
CREATE OR REPLACE FUNCTION cleanup_old_sync_events()
RETURNS void AS $$
BEGIN
    DELETE FROM sync_events
    WHERE status = 'completed'
        AND created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    DELETE FROM sync_events
    WHERE status = 'failed'
        AND retries >= 3
        AND created_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Вставка маппинга рангов (пример для 20 рангов TTFD)
-- ============================================================================

-- ВАЖНО: Замените discord_role_id на реальные ID ролей с вашего Discord сервера
-- Получить ID ролей: в Discord → Настройки сервера → Роли → ПКМ на роль → Копировать ID

INSERT INTO rank_role_mappings (rank_id, rank_name, discord_role_id, discord_role_name, priority) VALUES
    (1, 'Пустой взгляд', '0000000000000000001', 'Пустой взгляд', 1),
    (2, 'Потерянный', '0000000000000000002', 'Потерянный', 2),
    (3, 'Холодный', '0000000000000000003', 'Холодный', 3),
    (4, 'Без сна', '0000000000000000004', 'Без сна', 4),
    (5, 'Ночной', '0000000000000000005', 'Ночной', 5),
    (6, 'Тихий', '0000000000000000006', 'Тихий', 6),
    (7, 'Гулёныш', '0000000000000000007', 'Гулёныш', 7),
    (8, 'Отрешённый', '0000000000000000008', 'Отрешённый', 8),
    (9, 'Бледный', '0000000000000000009', 'Бледный', 9),
    (10, 'Полумёртвый', '0000000000000000010', 'Полумёртвый', 10),
    (11, 'Гуль', '0000000000000000011', 'Гуль', 11),
    (12, 'Безэмо', '0000000000000000012', 'Безэмо', 12),
    (13, 'Пожиратель тишины', '0000000000000000013', 'Пожиратель тишины', 13),
    (14, 'Сломанный', '0000000000000000014', 'Сломанный', 14),
    (15, 'Чёрное сердце', '0000000000000000015', 'Чёрное сердце', 15),
    (16, 'Носитель тьмы', '0000000000000000016', 'Носитель тьмы', 16),
    (17, 'Первый кошмар', '0000000000000000017', 'Первый кошмар', 17),
    (18, 'Глава ночи', '0000000000000000018', 'Глава ночи', 18),
    (19, 'Король пустоты', '0000000000000000019', 'Король пустоты', 19),
    (20, 'Абсолютный гуль', '0000000000000000020', 'Абсолютный гуль', 20)
ON CONFLICT (rank_id) DO NOTHING;

-- ============================================================================
-- Готово!
-- ============================================================================

SELECT 'Миграция 006: Двусторонняя синхронизация применена успешно!' AS status;
SELECT COUNT(*) AS total_rank_mappings FROM rank_role_mappings;
