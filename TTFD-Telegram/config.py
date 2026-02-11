"""
Конфигурация Telegram бота
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Telegram Bot настройки
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_ADMIN_IDS_STR = os.getenv('TELEGRAM_ADMIN_IDS', '')
TELEGRAM_ADMIN_IDS = [id.strip() for id in TELEGRAM_ADMIN_IDS_STR.split(',') if id.strip()]

# Discord интеграция (опционально)
DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID', '0')

# Пути к файлам
DATABASE_FILE = 'data/user_data.json'
TICKETS_FILE = 'data/tickets.json'
SHOP_FILE = 'data/shop.json'

# Настройки наград
DAILY_REWARD_XP = 100
DAILY_REWARD_COINS = 50
DAILY_COOLDOWN_HOURS = 24

# Настройки магазина
SHOP_ENABLED = True

print("✅ Конфигурация загружена")
if TELEGRAM_ADMIN_IDS:
    print(f"   Админы: {', '.join(TELEGRAM_ADMIN_IDS)}")
