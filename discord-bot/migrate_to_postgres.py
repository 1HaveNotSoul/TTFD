#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт миграции данных из JSON в PostgreSQL
"""

import sys
import os
import json

# Добавляем папку py в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))

def migrate():
    """Мигрировать данные из JSON в PostgreSQL"""
    
    print("="*60)
    print("🔄 МИГРАЦИЯ ДАННЫХ JSON → PostgreSQL")
    print("="*60)
    print()
    
    # Проверяем DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL не установлен!")
        print()
        print("Установи переменную окружения:")
        print("  export DATABASE_URL='postgresql://user:pass@host:port/db'")
        print()
        print("Или добавь в .env файл:")
        print("  DATABASE_URL=postgresql://user:pass@host:port/db")
        print()
        return False
    
    print(f"✅ DATABASE_URL найден")
    print()
    
    # Импортируем базы данных
    try:
        from database_postgres import PostgresDatabase
        print("✅ PostgreSQL модуль загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки PostgreSQL: {e}")
        return False
    
    try:
        from database import Database as JSONDatabase
        print("✅ JSON модуль загружен")
    except Exception as e:
        print(f"❌ Ошибка загрузки JSON: {e}")
        return False
    
    print()
    
    # Создаём экземпляры
    try:
        pg_db = PostgresDatabase()
        print("✅ PostgreSQL подключение установлено")
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False
    
    try:
        json_db = JSONDatabase()
        print("✅ JSON база данных загружена")
    except Exception as e:
        print(f"❌ Ошибка загрузки JSON: {e}")
        return False
    
    print()
    print("-"*60)
    print("📊 СТАТИСТИКА")
    print("-"*60)
    
    # Получаем всех пользователей из JSON
    json_users = json_db.get_all_users()
    print(f"📦 Пользователей в JSON: {len(json_users)}")
    
    # Получаем всех пользователей из PostgreSQL
    pg_users = pg_db.get_all_users()
    print(f"🗄️  Пользователей в PostgreSQL: {len(pg_users)}")
    
    print()
    print("-"*60)
    print("🚀 НАЧИНАЕМ МИГРАЦИЮ")
    print("-"*60)
    print()
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for user_id, user_data in json_users.items():
        try:
            # Проверяем существует ли пользователь в PostgreSQL
            existing_user = pg_users.get(user_id)
            
            if existing_user:
                # Пользователь уже есть, обновляем только если JSON данные новее
                json_xp = user_data.get('xp', 0)
                pg_xp = existing_user.get('xp', 0)
                
                if json_xp > pg_xp:
                    print(f"🔄 Обновление {user_id}: XP {pg_xp} → {json_xp}")
                    pg_db.save_user(user_id, user_data)
                    migrated += 1
                else:
                    print(f"⏭️  Пропуск {user_id}: данные актуальны")
                    skipped += 1
            else:
                # Новый пользователь, добавляем
                print(f"➕ Добавление {user_id}: XP {user_data.get('xp', 0)}, Coins {user_data.get('coins', 0)}")
                pg_db.save_user(user_id, user_data)
                migrated += 1
        
        except Exception as e:
            print(f"❌ Ошибка миграции {user_id}: {e}")
            errors += 1
    
    print()
    print("-"*60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА")
    print("-"*60)
    print()
    print(f"✅ Мигрировано: {migrated}")
    print(f"⏭️  Пропущено: {skipped}")
    print(f"❌ Ошибок: {errors}")
    print()
    
    # Миграция голосовой активности
    print("-"*60)
    print("🎤 МИГРАЦИЯ ГОЛОСОВОЙ АКТИВНОСТИ")
    print("-"*60)
    print()
    
    voice_file = 'json/voice_data.json'
    if os.path.exists(voice_file):
        try:
            with open(voice_file, 'r', encoding='utf-8') as f:
                voice_data = json.load(f)
            
            voice_migrated = 0
            for user_id, data in voice_data.items():
                try:
                    pg_db.save_voice_data(user_id, data)
                    print(f"🎤 {user_id}: {data.get('total_time', 0)} секунд")
                    voice_migrated += 1
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
            
            print()
            print(f"✅ Мигрировано голосовых данных: {voice_migrated}")
        except Exception as e:
            print(f"❌ Ошибка миграции голосовых данных: {e}")
    else:
        print("⏭️  Файл voice_data.json не найден")
    
    print()
    print("="*60)
    print("🎉 МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print("="*60)
    print()
    print("📝 СЛЕДУЮЩИЕ ШАГИ:")
    print()
    print("1. Проверь данные в PostgreSQL")
    print("2. Обнови bot.py:")
    print("   from database_postgres import db")
    print("3. Перезапусти бота")
    print("4. Протестируй команды (!profile, !balance)")
    print("5. Если всё работает - удали JSON файлы")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = migrate()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print("⚠️ Миграция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
