-- Таблица для системы кодов привязки
-- Используется для быстрой привязки Discord к Telegram через одноразовые коды

CREATE TABLE IF NOT EXISTS link_codes (
    code TEXT PRIMARY KEY,                      -- Код привязки (ABC123)
    telegram_id TEXT NOT NULL,                  -- ID пользователя Telegram
    discord_id TEXT,                            -- ID пользователя Discord (после использования)
    platform TEXT NOT NULL,                     -- Платформа создания (telegram/discord)
    used BOOLEAN NOT NULL DEFAULT FALSE,        -- Использован ли код
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- Время создания
    expires_at TIMESTAMP NOT NULL,              -- Время истечения
    used_at TIMESTAMP                           -- Время использования
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_link_codes_telegram ON link_codes(telegram_id);
CREATE INDEX IF NOT EXISTS idx_link_codes_discord ON link_codes(discord_id);
CREATE INDEX IF NOT EXISTS idx_link_codes_expires ON link_codes(expires_at);
CREATE INDEX IF NOT EXISTS idx_link_codes_used ON link_codes(used);

-- Комментарии
COMMENT ON TABLE link_codes IS 'Одноразовые коды для быстрой привязки Discord к Telegram';
COMMENT ON COLUMN link_codes.code IS 'Уникальный код из 6 символов (заглавные буквы и цифры)';
COMMENT ON COLUMN link_codes.telegram_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN link_codes.discord_id IS 'ID пользователя в Discord (заполняется после использования)';
COMMENT ON COLUMN link_codes.platform IS 'Платформа на которой был создан код (telegram/discord)';
COMMENT ON COLUMN link_codes.used IS 'Флаг использования кода';
COMMENT ON COLUMN link_codes.created_at IS 'Время создания кода';
COMMENT ON COLUMN link_codes.expires_at IS 'Время истечения кода (обычно +10 минут от создания)';
COMMENT ON COLUMN link_codes.used_at IS 'Время использования кода';
