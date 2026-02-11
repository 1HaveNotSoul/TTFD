"""Тестовый скрипт для проверки структуры данных"""
import asyncio
import sys
import os

# Добавляем пути
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'telegram-bot'))

async def test_telegram():
    """Проверка структуры данных Telegram"""
    try:
        from infrastructure.database.connection import db_connection
        
        await db_connection.connect()
        pool = db_connection.get_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users LIMIT 1")
            
            if rows:
                print("Telegram БД - Колонки:")
                for key in rows[0].keys():
                    print(f"  - {key}: {type(rows[0][key]).__name__}")
            else:
                print("Telegram БД пустая")
        
        await db_connection.disconnect()
        
    except Exception as e:
        print(f"Ошибка Telegram: {e}")


async def test_discord():
    """Проверка структуры данных Discord"""
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'TTFD-Discord', 'py'))
        from database_postgres import db as discord_db
        
        users = discord_db.get_all_users()
        
        if users:
            first_user_id = list(users.keys())[0]
            first_user = users[first_user_id]
            
            print("\nDiscord БД - Поля:")
            for key, value in first_user.items():
                print(f"  - {key}: {type(value).__name__} = {value}")
        else:
            print("\nDiscord БД пустая")
            
    except Exception as e:
        print(f"\nОшибка Discord: {e}")


async def main():
    await test_telegram()
    await test_discord()


if __name__ == "__main__":
    asyncio.run(main())
