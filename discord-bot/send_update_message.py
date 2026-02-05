#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для отправки сообщения об обновлении в Discord канал
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем папку py в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))

import discord
from discord.ext import commands
from font_converter import convert_to_font

# ID канала для обновлений
UPDATES_CHANNEL_ID = 1466923990936326294

# Текст сообщения
UPDATE_MESSAGE = """═══════════════════════════════════════════════════════════════
🎉 ОБНОВЛЕНИЕ - ДЕПЛОЙ НА RAILWAY.APP
═══════════════════════════════════════════════════════════════

📅 Дата: 05.02.2026
✅ Статус: БОТ ЗАПУЩЕН НА RAILWAY.APP

═══════════════════════════════════════════════════════════════
📋 СПИСОК ИЗМЕНЕНИЙ (03.02.2026 0:30 - 05.02.2026 06:32)
═══════════════════════════════════════════════════════════════

✅ 1. СОЗДАН ЕДИНЫЙ ПРОЕКТ TTFD
   📦 Объединены все компоненты в один репозиторий
   🔗 https://github.com/1HaveNotSoul/TTFD

✅ 2. ДОБАВЛЕНА КОНФИГУРАЦИЯ RAILWAY.APP
   📝 Полная документация для деплоя (30+ страниц)
   🌐 Платформа: Railway.app ($5 бесплатно/месяц)

✅ 3. ДОБАВЛЕН REQUIREMENTS.TXT
   📦 discord.py, aiohttp, python-dotenv, psycopg2, requests

✅ 4. ИСПРАВЛЕНА ВЕРСИЯ PYTHON
   🐍 Python 3.11.9 (совместимость с discord.py)

✅ 5. ДОБАВЛЕНА БИБЛИОТЕКА REQUESTS
   📦 requests==2.31.0 для HTTP запросов

✅ 6. ИСПРАВЛЕН ЗАПУСК БОТА
   🔧 Обновлён main.py для Railway
   🔐 Токен из Environment Variables

═══════════════════════════════════════════════════════════════
🚀 ТЕКУЩИЙ СТАТУС
═══════════════════════════════════════════════════════════════

✅ Бот запущен на Railway.app
✅ Все системы работают (команды, ранги, тикеты, магазин)
✅ Работает 24/7 на облачном сервере

═══════════════════════════════════════════════════════════════
📊 СТАТИСТИКА
═══════════════════════════════════════════════════════════════

Коммитов: 6 | Файлов: 10+ | Документации: 500+ строк
Время работы: ~6 часов

═══════════════════════════════════════════════════════════════
📝 СЛЕДУЮЩИЕ ШАГИ
═══════════════════════════════════════════════════════════════

⏳ Подключение PostgreSQL
⏳ Деплой Website
⏳ Интеграция Website ↔ Bot

═══════════════════════════════════════════════════════════════

🎉 БОТ УСПЕШНО ЗАДЕПЛОЕН!
🚀 TTFD PROJECT - ВЕРСИЯ 2.0

═══════════════════════════════════════════════════════════════"""


async def send_update():
    """Отправить сообщение об обновлении"""
    # Получаем токен
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ DISCORD_TOKEN не найден в .env файле!")
        return
    
    # Создаём бота
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Бот подключен: {bot.user.name}")
        
        try:
            # Получаем канал
            channel = bot.get_channel(UPDATES_CHANNEL_ID)
            
            if not channel:
                print(f"❌ Канал {UPDATES_CHANNEL_ID} не найден!")
                await bot.close()
                return
            
            print(f"✅ Канал найден: {channel.name}")
            
            # Отправляем сообщение
            await channel.send(UPDATE_MESSAGE)
            print("✅ Сообщение отправлено!")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        finally:
            await bot.close()
    
    # Запускаем бота
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")


if __name__ == "__main__":
    import asyncio
    
    print("🚀 Отправка сообщения об обновлении...")
    asyncio.run(send_update())
    print("✅ Готово!")
