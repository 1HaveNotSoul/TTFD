# Конфигурация Discord бота
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

# Проверка обязательных настроек
if not DISCORD_TOKEN:
    print(" DISCORD_TOKEN не установлен!")
    print(" Создай .env файл и добавь DISCORD_TOKEN")
    print(" Получить токен: https://discord.com/developers/applications")

if GUILD_ID == 0:
    print(" GUILD_ID не установлен")
    print(" Добавь GUILD_ID в .env файл")
    print("   Как получить: Discord  Settings  Advanced  Developer Mode  ПКМ на сервер  Copy Server ID")
