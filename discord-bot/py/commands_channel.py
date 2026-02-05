# Система канала команд с авто-удалением

import discord
from discord.ext import commands
import asyncio

# ID канала для команд
COMMANDS_CHANNEL_ID = 1467772214047801516

# Время до удаления (в секундах)
DELETE_AFTER = 300  # 5 минут

async def handle_command_message(message, bot_response=None):
    """
    Обработка сообщения команды с авто-удалением
    
    Args:
        message: Сообщение пользователя с командой
        bot_response: Ответ бота (если есть)
    """
    # Удаляем сообщение пользователя через 5 минут
    try:
        await asyncio.sleep(DELETE_AFTER)
        await message.delete()
    except:
        pass
    
    # Удаляем ответ бота через 5 минут (если есть)
    if bot_response:
        try:
            await asyncio.sleep(DELETE_AFTER)
            await bot_response.delete()
        except:
            pass

def is_commands_channel(channel_id):
    """Проверка, является ли канал каналом команд"""
    return channel_id == COMMANDS_CHANNEL_ID

async def setup_commands_channel_permissions(bot):
    """Настроить права доступа к каналу команд"""
    try:
        channel = bot.get_channel(COMMANDS_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Канал команд не найден (ID: {COMMANDS_CHANNEL_ID})")
            return False
        
        guild = channel.guild
        
        # Настраиваем права: пользователи не видят сообщения друг друга
        # Это делается через настройки канала в Discord:
        # 1. Отключить "Read Message History" для @everyone
        # 2. Включить "Send Messages" для @everyone
        
        print(f"✅ Канал команд найден: {channel.name}")
        print(f"⚠️ Настрой права вручную:")
        print(f"   1. Отключи 'Read Message History' для @everyone")
        print(f"   2. Включи 'Send Messages' для @everyone")
        print(f"   3. Пользователи не будут видеть сообщения друг друга")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настройки канала команд: {e}")
        return False
