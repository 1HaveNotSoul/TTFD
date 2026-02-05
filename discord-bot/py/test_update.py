"""
Тестовый скрипт для проверки обновления списка команд
"""

import asyncio
import discord
from discord.ext import commands
import config
from commands_manager import get_commands_text

# ID канала команд
COMMANDS_CHANNEL_ID = 1466295322002067607

async def test_update():
    """Тест обновления списка команд"""
    
    # Создаём бота
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        print("="*50)
        print("✅ Бот подключен!")
        print(f"📛 Имя: {bot.user.name}")
        print("="*50)
        
        # Получаем канал
        channel = bot.get_channel(COMMANDS_CHANNEL_ID)
        
        if not channel:
            print(f"❌ Канал не найден (ID: {COMMANDS_CHANNEL_ID})")
            await bot.close()
            return
        
        print(f"✅ Канал найден: {channel.name}")
        
        # Генерируем текст
        print("📄 Генерация текста...")
        text = get_commands_text()
        print(f"✅ Текст сгенерирован ({len(text)} символов)")
        print("\nПредпросмотр:")
        print("-"*50)
        print(text[:500])
        print("-"*50)
        
        # Отправляем сообщение
        print("\n📤 Отправка сообщения...")
        try:
            message = await channel.send(text)
            print(f"✅ Сообщение отправлено! ID: {message.id}")
            print(f"🔗 Ссылка: {message.jump_url}")
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
        
        print("\n✅ Тест завершён!")
        await bot.close()
    
    # Запускаем бота
    try:
        await bot.start(config.DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    print("🧪 Запуск теста обновления списка команд...")
    asyncio.run(test_update())
