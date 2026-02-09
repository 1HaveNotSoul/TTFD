"""
Миграция данных из JSON в PostgreSQL
"""
import json
import asyncio
import asyncpg
import os
import sys
from datetime import datetime

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import Config


async def migrate():
    """Мигрировать данные из JSON в PostgreSQL"""
    print("=" * 60)
    print("🔄 Миграция данных JSON → PostgreSQL")
    print("=" * 60)
    
    # Подключаемся к PostgreSQL
    print(f"\n📡 Подключение к {Config.DATABASE_URL}...")
    conn = await asyncpg.connect(Config.DATABASE_URL)
    print("✅ Подключено")
    
    # Читаем JSON
    json_file = 'data/user_data.json'
    if not os.path.exists(json_file):
        print(f"❌ Файл {json_file} не найден!")
        await conn.close()
        return
    
    print(f"\n📖 Чтение {json_file}...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    users_data = data.get('users', {})
    print(f"✅ Найдено {len(users_data)} пользователей")
    
    # Мигрируем пользователей
    print("\n👥 Миграция пользователей...")
    migrated = 0
    skipped = 0
    
    for telegram_id, user_data in users_data.items():
        try:
            # Парсим даты
            created_at = user_data.get('created_at')
            if created_at:
                created_at = datetime.fromisoformat(created_at)
            else:
                created_at = datetime.now()
            
            last_active = user_data.get('last_active')
            if last_active:
                last_active = datetime.fromisoformat(last_active)
            else:
                last_active = datetime.now()
            
            last_daily = user_data.get('last_daily')
            if last_daily:
                last_daily = datetime.fromisoformat(last_daily)
            
            last_spin = user_data.get('last_spin')
            if last_spin:
                last_spin = datetime.fromisoformat(last_spin)
            
            # Вставляем пользователя
            await conn.execute(
                """
                INSERT INTO users (
                    telegram_id, username, first_name, xp, coins, rank_id,
                    discord_id, created_at, last_active, last_daily, last_spin
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    xp = EXCLUDED.xp,
                    coins = EXCLUDED.coins,
                    rank_id = EXCLUDED.rank_id,
                    last_active = EXCLUDED.last_active
                """,
                telegram_id,
                user_data.get('username', 'Unknown'),
                user_data.get('first_name', ''),
                user_data.get('xp', 0),
                user_data.get('coins', 0),
                user_data.get('rank_id', 1),
                user_data.get('discord_id'),
                created_at,
                last_active,
                last_daily,
                last_spin
            )
            
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"   Мигрировано: {migrated}/{len(users_data)}")
        
        except Exception as e:
            print(f"   ⚠️  Ошибка при миграции {telegram_id}: {e}")
            skipped += 1
    
    print(f"\n✅ Миграция завершена!")
    print(f"   • Успешно: {migrated}")
    print(f"   • Пропущено: {skipped}")
    
    # Обновляем глобальную статистику
    print("\n📊 Обновление глобальной статистики...")
    total_xp = await conn.fetchval("SELECT SUM(xp) FROM users")
    total_coins = await conn.fetchval("SELECT SUM(coins) FROM users")
    total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
    
    await conn.execute(
        "UPDATE global_stats SET value = $1 WHERE key = 'total_users'",
        total_users
    )
    await conn.execute(
        "UPDATE global_stats SET value = $1 WHERE key = 'total_xp_earned'",
        total_xp or 0
    )
    await conn.execute(
        "UPDATE global_stats SET value = $1 WHERE key = 'total_coins_earned'",
        total_coins or 0
    )
    
    print(f"✅ Статистика обновлена")
    print(f"   • Всего пользователей: {total_users}")
    print(f"   • Всего XP: {total_xp or 0}")
    print(f"   • Всего монет: {total_coins or 0}")
    
    # Закрываем подключение
    await conn.close()
    print("\n" + "=" * 60)
    print("✅ Миграция успешно завершена!")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(migrate())
