# Discord Bot - Main Entry Point
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def main():
    print("=" * 50)
    print(" Запуск Discord Бота TTFD")
    print("=" * 50)
    
    # Проверяем наличие токена
    import config
    if not config.DISCORD_TOKEN:
        print(" DISCORD_TOKEN не установлен!")
        print(" Создай .env файл и добавь DISCORD_TOKEN")
        return
    
    # Запускаем бота
    print(" Запуск бота...")
    import bot
    bot.bot.run(config.DISCORD_TOKEN)

if __name__ == "__main__":
    main()
