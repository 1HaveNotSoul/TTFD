# Главный файл - запускает бота и веб-сервер одновременно
import asyncio
import threading
from datetime import datetime
import os

def run_web_server():
    """Запуск веб-сервера"""
    from app import app
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_bot():
    """Запуск Discord бота"""
    import bot as bot_module
    bot_module.run_bot()

def main():
    """Главная функция"""
    print("=" * 50)
    print("🚀 Запуск Discord бота с веб-панелью")
    print("=" * 50)

    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("✅ Веб-сервер запущен")

    # Проверяем наличие DISCORD_TOKEN перед запуском бота
    import config
    if config.DISCORD_TOKEN:
        # Запускаем бота (блокирующий вызов)
        print("🤖 Запуск Discord бота...")
        run_bot()
    else:
        print("⚠️ Discord бот отключен (нет DISCORD_TOKEN)")
        print("💡 Работает только веб-сервер")
        # Держим процесс живым
        import time
        while True:
            time.sleep(60)

if __name__ == "__main__":
    main()
