# Конфигурация проекта
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Discord настройки
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID_STR = os.getenv('GUILD_ID', '0')

# Безопасное преобразование GUILD_ID
try:
    GUILD_ID = int(GUILD_ID_STR) if GUILD_ID_STR.isdigit() else 0
except (ValueError, AttributeError):
    GUILD_ID = 0

# Веб-сервер настройки
WEB_PORT = int(os.getenv('WEB_PORT', 5000))
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Проверка обязательных настроек
if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN не установлен в .env файле!")

if GUILD_ID == 0:
    print("⚠️ GUILD_ID не установлен, некоторые функции могут не работать")
