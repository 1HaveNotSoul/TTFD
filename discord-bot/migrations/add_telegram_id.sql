-- Миграция: Добавление колонки telegram_id для привязки Telegram аккаунтов
-- Дата: 2026-02-10

-- Добавляем колонку telegram_id (может быть NULL если не привязан)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS telegram_id TEXT;

-- Создаём индекс для быстрого поиска по telegram_id
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- Комментарий к колонке
COMMENT ON COLUMN users.telegram_id IS 'ID привязанного Telegram аккаунта (NULL если не привязан)';
