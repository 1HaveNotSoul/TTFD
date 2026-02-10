"""
Применить миграцию: добавить колонку telegram_id в таблицу users
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def apply_migration():
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL не найден в .env")
        return False
    
    # Исправляем URL для psycopg2
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        print("🔄 Подключение к PostgreSQL...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("🔄 Применение миграции add_telegram_id.sql...")
        
        # Читаем SQL файл
        with open('migrations/add_telegram_id.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Выполняем миграцию
        cur.execute(sql)
        conn.commit()
        
        print("✅ Миграция успешно применена!")
        
        # Проверяем что колонка добавлена
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'telegram_id'
        """)
        
        result = cur.fetchone()
        if result:
            print(f"✅ Колонка telegram_id создана:")
            print(f"   Тип: {result[1]}")
            print(f"   Nullable: {result[2]}")
        else:
            print("⚠️ Колонка не найдена (возможно уже существовала)")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🔧 Миграция БД Discord: Добавление telegram_id")
    print("=" * 60)
    
    success = apply_migration()
    
    if success:
        print("\n✅ Готово! Теперь можно использовать команду /code в Telegram")
    else:
        print("\n❌ Миграция не удалась")
