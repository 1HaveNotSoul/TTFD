"""
Скрипт для применения миграции link_codes таблицы
Создаёт таблицу для системы кодов привязки
"""

import asyncio
import asyncpg
import os
from pathlib import Path

async def apply_migration():
    """Применить миграцию link_codes"""
    
    # Получаем DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL не найден в переменных окружения")
        print("💡 Установи переменную окружения:")
        print("   PowerShell: $env:DATABASE_URL='postgresql://...'")
        return False
    
    print("=" * 70)
    print("🔄 ПРИМЕНЕНИЕ МИГРАЦИИ: link_codes таблица")
    print("=" * 70)
    print(f"📊 База данных: {database_url[:30]}...")
    print()
    
    try:
        # Подключаемся к БД
        print("🔌 Подключение к PostgreSQL...")
        conn = await asyncpg.connect(database_url)
        print("✅ Подключено успешно")
        print()
        
        # Читаем SQL файл
        sql_file = Path(__file__).parent / 'create_link_codes_table.sql'
        print(f"📄 Чтение SQL файла: {sql_file.name}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"✅ SQL файл прочитан ({len(sql)} символов)")
        print()
        
        # Применяем миграцию
        print("🔄 Применение миграции...")
        await conn.execute(sql)
        print("✅ Миграция применена успешно!")
        print()
        
        # Проверяем таблицу
        print("🔍 Проверка таблицы...")
        result = await conn.fetchrow("""
            SELECT 
                COUNT(*) as count,
                pg_size_pretty(pg_total_relation_size('link_codes')) as size
            FROM link_codes
        """)
        
        print(f"✅ Таблица link_codes создана")
        print(f"   📊 Записей: {result['count']}")
        print(f"   💾 Размер: {result['size']}")
        print()
        
        # Проверяем индексы
        print("🔍 Проверка индексов...")
        indexes = await conn.fetch("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'link_codes'
        """)
        
        print(f"✅ Создано индексов: {len(indexes)}")
        for idx in indexes:
            print(f"   • {idx['indexname']}")
        print()
        
        # Закрываем соединение
        await conn.close()
        
        print("=" * 70)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 70)
        print()
        print("🎯 Следующие шаги:")
        print("   1. Залить изменения на GitHub")
        print("   2. Задеплоить на Railway")
        print("   3. Протестировать команды /linkcode и /link")
        print()
        
        return True
    
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ОШИБКА ПРИМЕНЕНИЯ МИГРАЦИИ")
        print("=" * 70)
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Сообщение: {e}")
        print()
        
        import traceback
        print("Полный traceback:")
        traceback.print_exc()
        
        return False


if __name__ == "__main__":
    success = asyncio.run(apply_migration())
    
    if success:
        print("✅ Готово! Таблица link_codes создана.")
    else:
        print("❌ Миграция не применена. Проверь ошибки выше.")
