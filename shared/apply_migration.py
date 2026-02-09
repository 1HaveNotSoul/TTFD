"""
Альтернативный способ применения миграции без psql
Использует только Python и asyncpg
"""
import asyncio
import os
import sys
import asyncpg
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def apply_migration():
    """Применить SQL миграцию через Python"""
    logger.info("=" * 60)
    logger.info("📝 ПРИМЕНЕНИЕ МИГРАЦИИ UNIFIED DATABASE")
    logger.info("=" * 60)
    logger.info("")
    
    # Получаем DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        logger.error("❌ DATABASE_URL не установлен!")
        logger.error("")
        logger.error("💡 Установи переменную окружения:")
        logger.error("   set DATABASE_URL=postgresql://...")
        logger.error("")
        return False
    
    logger.info("✅ DATABASE_URL найден")
    logger.info("")
    
    try:
        # Подключаемся к БД
        logger.info("🔌 Подключение к PostgreSQL...")
        conn = await asyncpg.connect(database_url)
        logger.info("✅ Подключено")
        logger.info("")
        
        # Читаем SQL файл
        logger.info("📖 Чтение migration_unified.sql...")
        sql_file = os.path.join(os.path.dirname(__file__), 'migration_unified.sql')
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        logger.info("✅ SQL файл прочитан")
        logger.info("")
        
        # Применяем миграцию
        logger.info("🚀 Применение миграции...")
        await conn.execute(sql)
        logger.info("✅ Миграция применена")
        logger.info("")
        
        # Проверяем таблицы
        logger.info("🔍 Проверка таблиц...")
        
        # Проверяем unified_users
        count_users = await conn.fetchval("SELECT COUNT(*) FROM unified_users")
        logger.info(f"   ✅ unified_users: {count_users} записей")
        
        # Проверяем cross_platform_events
        count_events = await conn.fetchval("SELECT COUNT(*) FROM cross_platform_events")
        logger.info(f"   ✅ cross_platform_events: {count_events} записей")
        
        logger.info("")
        
        # Закрываем подключение
        await conn.close()
        
        logger.info("=" * 60)
        logger.info("✅ МИГРАЦИЯ УСПЕШНО ПРИМЕНЕНА!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("📊 Что дальше:")
        logger.info("   1. Запусти: python migrate_to_unified.py")
        logger.info("   2. Проверь данные в Railway (вкладка Data)")
        logger.info("   3. Открой TTFD\\СЛЕДУЮЩИЕ_ШАГИ_ИНТЕГРАЦИЯ.md")
        logger.info("")
        
        return True
        
    except asyncpg.exceptions.DuplicateTableError:
        logger.warning("⚠️  Таблицы уже существуют")
        logger.info("")
        logger.info("💡 Это нормально, если ты уже применял миграцию")
        logger.info("   Можешь сразу запустить: python migrate_to_unified.py")
        logger.info("")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка применения миграции: {e}")
        logger.error("")
        logger.error("💡 Возможные причины:")
        logger.error("   - Неправильный DATABASE_URL")
        logger.error("   - Нет доступа к Railway")
        logger.error("   - asyncpg не установлен (pip install asyncpg)")
        logger.error("")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Главная функция"""
    success = await apply_migration()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
