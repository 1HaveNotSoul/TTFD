# Главный файл - запускает бота и веб-сервер одновременно
import asyncio
import threading
from datetime import datetime
import bot as bot_module
import web

# Импортируем Telegram бэкап
try:
    from telegram_bot import auto_backup_to_telegram
    telegram_enabled = True
except Exception as e:
    print(f"⚠️ Telegram бэкап недоступен: {e}")
    telegram_enabled = False

def update_web_stats():
    """Обновление статистики для веб-сайта"""
    while True:
        try:
            if bot_module.bot.is_ready():
                uptime = 0
                if bot_module.bot.stats['start_time']:
                    uptime = int((datetime.now() - bot_module.bot.stats['start_time']).total_seconds())
                
                web.update_bot_data({
                    'status': 'online' if bot_module.bot.is_ready() else 'offline',
                    'uptime': uptime,
                    'guilds': len(bot_module.bot.guilds),
                    'users': len(bot_module.bot.users),
                    'commands_used': bot_module.bot.stats['commands_used'],
                    'messages_seen': bot_module.bot.stats['messages_seen'],
                    'latency': round(bot_module.bot.latency * 1000),
                })
        except Exception as e:
            print(f"❌ Ошибка обновления статистики: {e}")
        
        # Обновляем каждые 5 секунд
        threading.Event().wait(5)

def run_web_server():
    """Запуск веб-сервера в отдельном потоке"""
    web.run_web()

def main():
    """Главная функция"""
    print("=" * 50)
    print("🚀 Запуск Discord бота с веб-панелью")
    print("=" * 50)
    
    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("✅ Веб-сервер запущен")
    
    # Запускаем обновление статистики в отдельном потоке
    stats_thread = threading.Thread(target=update_web_stats, daemon=True)
    stats_thread.start()
    print("✅ Обновление статистики запущено")
    
    # Запускаем бота (блокирующий вызов)
    print("🤖 Запуск Discord бота...")
    bot_module.run_bot()

if __name__ == "__main__":
    main()
