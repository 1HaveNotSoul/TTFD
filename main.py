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
    import time
    
    while True:
        try:
            import bot as bot_module
            print("🔄 Попытка подключения к Discord...")
            bot_module.run_bot()
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Ошибка запуска бота: {error_msg[:200]}...")
            
            # Проверяем на rate limit
            if "429" in error_msg or "rate limit" in error_msg.lower() or "1015" in error_msg:
                print("⚠️ Discord rate limit активен")
                print("💡 Ожидание 5 минут перед повторной попыткой...")
                time.sleep(300)  # 5 минут
                print("🔄 Повторная попытка подключения...")
            else:
                print("⚠️ Неизвестная ошибка, ожидание 60 секунд...")
                time.sleep(60)

def main():
    """Главная функция"""
    print("=" * 50)
    print("🚀 Запуск веб-сервера TTFD")
    print("=" * 50)

    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print("✅ Веб-сервер запущен")

    # Проверяем наличие DISCORD_TOKEN перед запуском бота
    import config
    if config.DISCORD_TOKEN:
        # Запускаем бота в отдельном потоке (не блокирующий)
        print("🤖 Запуск Discord бота в фоновом режиме...")
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("✅ Discord бот запущен в фоне")
    else:
        print("⚠️ Discord бот отключен (нет DISCORD_TOKEN)")
    
    print("💡 Веб-сервер работает на порту", os.environ.get('PORT', 10000))
    
    # Держим процесс живым
    import time
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
