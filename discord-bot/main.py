#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Главный файл запуска Discord бота
Запускает бота из папки py/
"""

import sys
import os

# Добавляем папку py в путь для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))

# Импортируем и запускаем бота
if __name__ == "__main__":
    from py.bot import bot
    
    # Получаем токен из переменных окружения
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ ERROR: DISCORD_TOKEN не найден в переменных окружения!")
        sys.exit(1)
    
    print("🚀 Запуск Discord бота...")
    
    # Запускаем бота
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)
