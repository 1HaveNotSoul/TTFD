#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки автообновления
"""

import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем папку py в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))

import discord
from discord.ext import commands
import asyncio
import updates_system

# Получаем токен
token = os.getenv('DISCORD_TOKEN')

if not token:
    print("❌ DISCORD_TOKEN не найден в .env файле!")
    sys.exit(1)

# Создаём бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Бот подключен: {bot.user.name}")
    print(f"🌐 Серверов: {len(bot.guilds)}")
    
    # Проверяем канал
    channel_id = 1466923990936326294
    channel = bot.get_channel(channel_id)
    
    if not channel:
        print(f"❌ Канал {channel_id} не найден!")
        print(f"📋 Доступные каналы:")
        for guild in bot.guilds:
            print(f"   Сервер: {guild.name}")
            for ch in guild.text_channels:
                print(f"      - {ch.name} (ID: {ch.id})")
    else:
        print(f"✅ Канал найден: {channel.name} (ID: {channel.id})")
        
        # Проверяем права
        permissions = channel.permissions_for(channel.guild.me)
        print(f"📝 Права бота в канале:")
        print(f"   - Send Messages: {permissions.send_messages}")
        print(f"   - Embed Links: {permissions.embed_links}")
        print(f"   - Attach Files: {permissions.attach_files}")
    
    # Проверяем файл автообновления
    print("\n📄 Проверка файла автообновления:")
    auto_update_info = updates_system.load_auto_update()
    print(f"   - enabled: {auto_update_info.get('enabled')}")
    print(f"   - version: {auto_update_info.get('version')}")
    print(f"   - changes: {len(auto_update_info.get('changes', []))} изменений")
    
    # Пытаемся отправить автообновление
    print("\n🔄 Попытка отправки автообновления...")
    try:
        success = await updates_system.check_auto_update(bot)
        if success:
            print("✅ Автообновление отправлено успешно!")
        else:
            print("❌ Автообновление не отправлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    # Закрываем бота
    await bot.close()

# Запускаем бота
print("🚀 Запуск тестового бота...")
try:
    bot.run(token)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
