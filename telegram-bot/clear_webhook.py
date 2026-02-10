"""
Очистить webhook Telegram бота
Используй это если получаешь ошибку "Conflict: terminated by other getUpdates request"
"""
import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

async def clear_webhook():
    """Очистить webhook и удалить pending updates"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env")
        return
    
    bot = Bot(token=token)
    
    try:
        print("🔄 Удаление webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook удалён")
        print("✅ Pending updates очищены")
        
        # Проверяем статус
        webhook_info = await bot.get_webhook_info()
        print(f"\n📊 Статус webhook:")
        print(f"   URL: {webhook_info.url or 'Не установлен'}")
        print(f"   Pending updates: {webhook_info.pending_update_count}")
        
        if not webhook_info.url:
            print("\n✅ Webhook очищен успешно!")
            print("💡 Теперь можешь запустить бота через polling")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        # Закрываем сессию
        await bot.close()

if __name__ == '__main__':
    print("=" * 60)
    print("🧹 Очистка Telegram Webhook")
    print("=" * 60)
    asyncio.run(clear_webhook())
