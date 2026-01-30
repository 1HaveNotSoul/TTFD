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
    try:
        import bot as bot_module
        bot_module.run_bot()
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Ошибка запуска бота: {error_msg}")
        
        # Проверяем на rate limit
        if "429" in error_msg or "rate limit" in error_msg.lower():
            print("⚠️ Discord rate limit - слишком частые подключения")
            print("💡 Ожидание 60 секунд перед повторной попыткой...")
            import time
            time.sleep(60)
            print("🔄 Повторная попытка подключения...")
            try:
                bot_module.run_bot()
            except Exception as e2:
                print(f"❌ Повторная попытка не удалась: {e2}")
                print("⚠️ Бот отключен, работает только веб-сервер")
        else:
            print("⚠️ Бот отключен, работает только веб-сервер")
        
        # Держим процесс живым
        import time
        while True:
            time.sleep(60)

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
