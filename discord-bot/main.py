#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Главный файл запуска Discord бота
Запускает бота из папки py/
"""

import sys
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Добавляем папку py в путь для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))

# Импортируем и запускаем бота
if __name__ == "__main__":
    from py.bot import bot
    
    # Получаем токен из переменных окружения
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ ERROR: DISCORD_TOKEN не найден в .env файле!")
        print("📝 Создай файл .env и добавь:")
        print("   DISCORD_TOKEN=твой_токен_бота")
        print("   GUILD_ID=твой_server_id")
        sys.exit(1)
    
    print("🚀 Запуск Discord бота...")
    print(f"🔑 Токен загружен: {token[:20]}...")
    
    # Запускаем бота
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        print("\n💡 Возможные причины:")
        print("   1. Неправильный токен в .env файле")
        print("   2. Токен устарел - получи новый на https://discord.com/developers/applications")
        print("   3. Бот не активирован в Discord Developer Portal")
        sys.exit(1)
