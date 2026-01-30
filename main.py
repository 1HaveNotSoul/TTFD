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
        print(f"❌ Ошибка запуска бота: {e}")
        print("⚠️ Бот отключен, работает только веб-сервер")
        import time
        while True:
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

    # Discord бот временно отключен (проблема совместимости с Python 3.13)
    print("⚠️ Discord бот отключен (несовместимость audioop с Python 3.13)")
    print("💡 Работает только веб-сервер")
    
    # Держим процесс живым
    import time
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
