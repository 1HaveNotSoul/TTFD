#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест подключения к PostgreSQL
Запусти этот скрипт чтобы проверить работает ли база данных
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

print("═══════════════════════════════════════════════════════════════")
print("🔍 ТЕСТ ПОДКЛЮЧЕНИЯ К POSTGRESQL")
print("═══════════════════════════════════════════════════════════════\n")

# Проверка DATABASE_URL
database_url = os.getenv('DATABASE_URL')

if not database_url:
    print("❌ DATABASE_URL не найден в .env файле")
    print("\n💡 Добавь в .env файл:")
    print("   DATABASE_URL=postgresql://user:password@host:port/database")
    print("\n📝 Скопируй DATABASE_URL из Railway:")
    print("   1. Открой Postgres на Railway")
    print("   2. Variables → DATABASE_URL → Copy")
    print("   3. Вставь в .env файл")
    sys.exit(1)

print(f"✅ DATABASE_URL найден")
print(f"   Host: {database_url.split('@')[1].split(':')[0] if '@' in database_url else 'unknown'}")

# Проверка psycopg2
print("\n🔍 Проверка psycopg2...")
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    print("✅ psycopg2 установлен")
except ImportError as e:
    print(f"❌ psycopg2 не установлен: {e}")
    print("\n💡 Установи psycopg2:")
    print("   pip install psycopg2-binary")
    sys.exit(1)

# Исправление URL для psycopg2
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    print("✅ URL исправлен для psycopg2 (postgres:// → postgresql://)")

# Попытка подключения
print("\n🔍 Попытка подключения к базе данных...")
try:
    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    print("✅ Подключение успешно!")
    
    # Проверка версии PostgreSQL
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"\n📊 Версия PostgreSQL:")
    print(f"   {version['version'].split(',')[0]}")
    
    # Проверка существующих таблиц
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    
    if tables:
        print(f"\n📋 Существующие таблицы ({len(tables)}):")
        for table in tables:
            print(f"   - {table['table_name']}")
    else:
        print("\n⚠️ Таблицы не найдены (база пустая)")
        print("   Это нормально для новой базы")
        print("   Таблицы создадутся при первом запуске бота")
    
    # Проверка подключения к database_postgres.py
    print("\n🔍 Проверка database_postgres.py...")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))
    
    try:
        from database_postgres import PostgresDatabase
        db = PostgresDatabase()
        print("✅ database_postgres.py работает")
        
        # Проверка таблиц после инициализации
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables_after = cur.fetchall()
        
        if len(tables_after) > len(tables):
            print(f"\n✅ Создано таблиц: {len(tables_after) - len(tables)}")
            for table in tables_after:
                if table not in tables:
                    print(f"   + {table['table_name']}")
        
        print("\n═══════════════════════════════════════════════════════════════")
        print("✅ ВСЁ РАБОТАЕТ!")
        print("═══════════════════════════════════════════════════════════════")
        print("\n💡 База данных готова к использованию")
        print("   Бот будет автоматически использовать PostgreSQL")
        print("   Данные не будут пропадать при деплое")
        
    except Exception as e:
        print(f"⚠️ Ошибка инициализации database_postgres.py: {e}")
        print("\n💡 Проверь:")
        print("   - Файл discord-bot/py/database_postgres.py существует")
        print("   - Нет синтаксических ошибок в коде")
        import traceback
        traceback.print_exc()
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"❌ Ошибка подключения: {e}")
    print("\n💡 Возможные причины:")
    print("   1. Неправильный DATABASE_URL")
    print("   2. PostgreSQL база ещё не готова (подожди 2-3 минуты)")
    print("   3. Проблемы с сетью")
    print("\n📝 Проверь DATABASE_URL на Railway:")
    print("   Railway → Postgres → Variables → DATABASE_URL")
    sys.exit(1)

except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n═══════════════════════════════════════════════════════════════")
print("🎉 ТЕСТ ЗАВЕРШЁН УСПЕШНО")
print("═══════════════════════════════════════════════════════════════")
