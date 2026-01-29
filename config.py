# Конфигурация проекта
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла (для локальной разработки)
# На Render переменные берутся напрямую из Environment Variables
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
# На Render используется переменная PORT, на локалке - WEB_PORT
PORT = os.getenv('PORT')  # Render автоматически устанавливает PORT
WEB_PORT = int(PORT) if PORT else int(os.getenv('WEB_PORT', 5000))
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Проверка обязательных настроек
if not DISCORD_TOKEN:
    print("❌ DISCORD_TOKEN не установлен!")
    print("💡 Добавь переменные окружения в Render Dashboard:")
    print("   - DISCORD_TOKEN")
    print("   - GUILD_ID")
    print("   - SECRET_KEY")
    raise ValueError("DISCORD_TOKEN is required")

if GUILD_ID == 0:
    print("⚠️ GUILD_ID не установлен, некоторые функции могут не работать")
