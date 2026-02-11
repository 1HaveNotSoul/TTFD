"""
Скрипт миграции данных в Unified Database
Переносит пользователей из всех платформ в единую таблицу unified_users
"""
import asyncio
import os
import sys
import logging
from datetime import datetime

# Добавляем пути к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'telegram-bot'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'TTFD-Discord', 'py'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'TTFD-Website'))

from database_unified import get_unified_db
from models import UnifiedUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_telegram_users():
    """Мигрировать пользователей из Telegram Bot"""
    logger.info("=" * 60)
    logger.info("📱 МИГРАЦИЯ TELEGRAM ПОЛЬЗОВАТЕЛЕЙ")
    logger.info("=" * 60)
    
    try:
        # Импортируем Telegram БД
        from infrastructure.database.connection import db_connection
        await db_connection.connect()
        pool = db_connection.get_pool()
        
        unified_db = await get_unified_db()
        
        # Получаем всех пользователей из Telegram БД
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM users")
        
        logger.info(f"📊 Найдено {len(rows)} пользователей в Telegram БД")
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for row in rows:
            user_id = None
            try:
                # В Telegram БД поле называется 'id', а не 'telegram_id'
                user_id = str(row['id'])
                
                # Проверяем существование
                existing = await unified_db.get_user_by_telegram(user_id)
                
                if existing:
                    logger.info(f"⏭️  Пропущен {user_id} (уже существует)")
                    skipped += 1
                    continue
                
                # Создаём пользователя
                user = await unified_db.create_user(
                    telegram_id=user_id,
                    username=row.get('username', 'Unknown'),
                    display_name=row.get('username', 'Unknown'),  # В Telegram БД нет first_name
                    primary_platform='telegram'
                )
                
                # Обновляем данные
                await unified_db.pool.execute("""
                    UPDATE unified_users
                    SET xp = $1, coins = $2, rank_id = $3,
                        games_played = $4, games_won = $5,
                        created_at = $6, last_active = $7, last_daily = $8,
                        daily_streak = $9
                    WHERE id = $10
                """, 
                    row.get('xp', 0),
                    row.get('coins', 0),
                    row.get('rank_id', 1),
                    row.get('games_played', 0),
                    row.get('games_won', 0),
                    row.get('created_at', datetime.now()),
                    row.get('last_active', datetime.now()),
                    row.get('last_daily'),
                    row.get('daily_streak', 0),
                    user.id
                )
                
                logger.info(f"✅ Мигрирован {user_id} → unified_id={user.id}")
                migrated += 1
                
            except Exception as e:
                if user_id:
                    logger.error(f"❌ Ошибка миграции {user_id}: {e}")
                else:
                    logger.error(f"❌ Ошибка миграции строки: {e}")
                errors += 1
        
        await db_connection.disconnect()
        
        logger.info("")
        logger.info("📊 СТАТИСТИКА МИГРАЦИИ TELEGRAM:")
        logger.info(f"   ✅ Мигрировано: {migrated}")
        logger.info(f"   ⏭️  Пропущено: {skipped}")
        logger.info(f"   ❌ Ошибок: {errors}")
        logger.info("")
        
        return {'migrated': migrated, 'skipped': skipped, 'errors': errors}
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка миграции Telegram: {e}")
        import traceback
        traceback.print_exc()
        return {'migrated': 0, 'skipped': 0, 'errors': 1}


async def migrate_discord_users():
    """Мигрировать пользователей из Discord Bot"""
    logger.info("=" * 60)
    logger.info("🎮 МИГРАЦИЯ DISCORD ПОЛЬЗОВАТЕЛЕЙ")
    logger.info("=" * 60)
    
    try:
        # Пытаемся импортировать Discord БД
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'TTFD-Discord', 'py'))
            from database_postgres import db as discord_db
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"⚠️  Discord БД недоступна: {e}")
            logger.info("💡 Пропускаем миграцию Discord пользователей")
            return {'migrated': 0, 'linked': 0, 'skipped': 0, 'errors': 0}
        
        unified_db = await get_unified_db()
        
        # Получаем всех пользователей из Discord БД
        users = discord_db.get_all_users()
        
        logger.info(f"📊 Найдено {len(users)} пользователей в Discord БД")
        
        migrated = 0
        linked = 0
        skipped = 0
        errors = 0
        
        for discord_id, user_data in users.items():
            try:
                # Проверяем существование по Discord ID
                existing = await unified_db.get_user_by_discord(discord_id)
                
                if existing:
                    logger.info(f"⏭️  Пропущен {discord_id} (уже существует)")
                    skipped += 1
                    continue
                
                # Проверяем есть ли пользователь с таким же username (может быть из Telegram)
                username = user_data.get('username', 'Unknown')
                
                # Пытаемся найти по username в unified_users
                async with unified_db.pool.acquire() as conn:
                    existing_by_username = await conn.fetchrow(
                        "SELECT * FROM unified_users WHERE username = $1 AND discord_id IS NULL",
                        username
                    )
                
                if existing_by_username:
                    # Привязываем Discord к существующему пользователю
                    success = await unified_db.link_discord(existing_by_username['id'], discord_id)
                    if success:
                        # Обновляем данные Discord
                        await unified_db.pool.execute("""
                            UPDATE unified_users
                            SET total_voice_time = total_voice_time + $1,
                                messages_sent = messages_sent + $2
                            WHERE id = $3
                        """,
                            user_data.get('voice_time', 0),
                            user_data.get('messages_sent', 0),
                            existing_by_username['id']
                        )
                        logger.info(f"🔗 Привязан Discord {discord_id} → unified_id={existing_by_username['id']}")
                        linked += 1
                    else:
                        logger.warning(f"⚠️  Не удалось привязать Discord {discord_id}")
                        errors += 1
                else:
                    # Создаём нового пользователя
                    user = await unified_db.create_user(
                        discord_id=discord_id,
                        username=username,
                        display_name=user_data.get('display_name', username),
                        primary_platform='discord'
                    )
                    
                    # Обновляем данные (без проблемных полей)
                    await unified_db.pool.execute("""
                        UPDATE unified_users
                        SET xp = $1, coins = $2, rank_id = $3,
                            games_played = $4, games_won = $5,
                            daily_streak = $6
                        WHERE id = $7
                    """,
                        user_data.get('xp', 0),
                        user_data.get('coins', 0),
                        user_data.get('rank_id', 1),
                        user_data.get('games_played', 0),
                        user_data.get('games_won', 0),
                        user_data.get('daily_streak', 0),
                        user.id
                    )
                    
                    logger.info(f"✅ Мигрирован {discord_id} → unified_id={user.id}")
                    migrated += 1
                
            except Exception as e:
                logger.error(f"❌ Ошибка миграции {discord_id}: {e}")
                errors += 1
        
        logger.info("")
        logger.info("📊 СТАТИСТИКА МИГРАЦИИ DISCORD:")
        logger.info(f"   ✅ Мигрировано: {migrated}")
        logger.info(f"   🔗 Привязано: {linked}")
        logger.info(f"   ⏭️  Пропущено: {skipped}")
        logger.info(f"   ❌ Ошибок: {errors}")
        logger.info("")
        
        return {'migrated': migrated, 'linked': linked, 'skipped': skipped, 'errors': errors}
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка миграции Discord: {e}")
        import traceback
        traceback.print_exc()
        return {'migrated': 0, 'linked': 0, 'skipped': 0, 'errors': 0}


async def migrate_website_users():
    """Мигрировать пользователей из Website"""
    logger.info("=" * 60)
    logger.info("🌐 МИГРАЦИЯ WEBSITE ПОЛЬЗОВАТЕЛЕЙ")
    logger.info("=" * 60)
    
    try:
        # Пытаемся импортировать Website БД
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'TTFD-Website'))
            from database import db as website_db
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"⚠️  Website БД недоступна: {e}")
            logger.info("💡 Пропускаем миграцию Website пользователей")
            return {'migrated': 0, 'linked': 0, 'skipped': 0, 'errors': 0}
        
        unified_db = await get_unified_db()
        
        # Получаем всех пользователей из Website БД
        # Пытаемся разные методы получения данных
        accounts = []
        try:
            if hasattr(website_db, 'get_all_accounts'):
                accounts = website_db.get_all_accounts()
            elif hasattr(website_db, 'get_all_users'):
                accounts = website_db.get_all_users()
            elif hasattr(website_db, 'accounts'):
                accounts = list(website_db.accounts.values())
            else:
                logger.warning("⚠️  Не найден метод получения аккаунтов")
                return {'migrated': 0, 'linked': 0, 'skipped': 0, 'errors': 0}
        except Exception as e:
            logger.warning(f"⚠️  Ошибка получения аккаунтов: {e}")
            return {'migrated': 0, 'linked': 0, 'skipped': 0, 'errors': 0}
        
        logger.info(f"📊 Найдено {len(accounts)} аккаунтов в Website БД")
        
        migrated = 0
        linked = 0
        skipped = 0
        errors = 0
        
        for account in accounts:
            try:
                email = account.get('email')
                if not email:
                    continue
                
                # Проверяем существование по email
                existing = await unified_db.get_user_by_website(email)
                
                if existing:
                    logger.info(f"⏭️  Пропущен {email} (уже существует)")
                    skipped += 1
                    continue
                
                # Проверяем есть ли Discord ID в аккаунте (привязка через OAuth)
                discord_id = account.get('discord_id')
                
                if discord_id:
                    # Ищем пользователя по Discord ID
                    existing_by_discord = await unified_db.get_user_by_discord(discord_id)
                    
                    if existing_by_discord:
                        # Привязываем Website к существующему пользователю
                        success = await unified_db.link_website(existing_by_discord.id, email)
                        if success:
                            logger.info(f"🔗 Привязан Website {email} → unified_id={existing_by_discord.id}")
                            linked += 1
                        else:
                            logger.warning(f"⚠️  Не удалось привязать Website {email}")
                            errors += 1
                        continue
                
                # Создаём нового пользователя
                user = await unified_db.create_user(
                    website_email=email,
                    username=account.get('username', 'Unknown'),
                    display_name=account.get('display_name', account.get('username', 'Unknown')),
                    primary_platform='website'
                )
                
                logger.info(f"✅ Мигрирован {email} → unified_id={user.id}")
                migrated += 1
                
            except Exception as e:
                logger.error(f"❌ Ошибка миграции {email if 'email' in locals() else 'unknown'}: {e}")
                errors += 1
        
        logger.info("")
        logger.info("📊 СТАТИСТИКА МИГРАЦИИ WEBSITE:")
        logger.info(f"   ✅ Мигрировано: {migrated}")
        logger.info(f"   🔗 Привязано: {linked}")
        logger.info(f"   ⏭️  Пропущено: {skipped}")
        logger.info(f"   ❌ Ошибок: {errors}")
        logger.info("")
        
        return {'migrated': migrated, 'linked': linked, 'skipped': skipped, 'errors': errors}
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка миграции Website: {e}")
        import traceback
        traceback.print_exc()
        return {'migrated': 0, 'linked': 0, 'skipped': 0, 'errors': 0}


async def main():
    """Главная функция миграции"""
    logger.info("")
    logger.info("=" * 60)
    logger.info("🚀 МИГРАЦИЯ В UNIFIED DATABASE")
    logger.info("=" * 60)
    logger.info("")
    
    # Проверяем DATABASE_URL
    if not os.getenv('DATABASE_URL'):
        logger.error("❌ DATABASE_URL не установлен!")
        logger.error("💡 Установи переменную окружения DATABASE_URL")
        return
    
    logger.info("✅ DATABASE_URL найден")
    logger.info("")
    
    # Применяем миграцию unified database
    logger.info("📝 Применение миграции unified database...")
    try:
        unified_db = await get_unified_db()
        logger.info("✅ Unified database подключена")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к unified database: {e}")
        return
    
    logger.info("")
    
    # Мигрируем пользователей
    telegram_stats = await migrate_telegram_users()
    discord_stats = await migrate_discord_users()
    website_stats = await migrate_website_users()
    
    # Итоговая статистика
    logger.info("=" * 60)
    logger.info("📊 ИТОГОВАЯ СТАТИСТИКА")
    logger.info("=" * 60)
    logger.info("")
    logger.info(f"📱 Telegram:")
    logger.info(f"   ✅ Мигрировано: {telegram_stats['migrated']}")
    logger.info(f"   ⏭️  Пропущено: {telegram_stats['skipped']}")
    logger.info(f"   ❌ Ошибок: {telegram_stats['errors']}")
    logger.info("")
    logger.info(f"🎮 Discord:")
    logger.info(f"   ✅ Мигрировано: {discord_stats['migrated']}")
    logger.info(f"   🔗 Привязано: {discord_stats.get('linked', 0)}")
    logger.info(f"   ⏭️  Пропущено: {discord_stats['skipped']}")
    logger.info(f"   ❌ Ошибок: {discord_stats['errors']}")
    logger.info("")
    logger.info(f"🌐 Website:")
    logger.info(f"   ✅ Мигрировано: {website_stats['migrated']}")
    logger.info(f"   🔗 Привязано: {website_stats.get('linked', 0)}")
    logger.info(f"   ⏭️  Пропущено: {website_stats['skipped']}")
    logger.info(f"   ❌ Ошибок: {website_stats['errors']}")
    logger.info("")
    
    total_migrated = telegram_stats['migrated'] + discord_stats['migrated'] + website_stats['migrated']
    total_linked = discord_stats.get('linked', 0) + website_stats.get('linked', 0)
    total_errors = telegram_stats['errors'] + discord_stats['errors'] + website_stats['errors']
    
    logger.info(f"🎯 ВСЕГО:")
    logger.info(f"   ✅ Мигрировано: {total_migrated}")
    logger.info(f"   🔗 Привязано: {total_linked}")
    logger.info(f"   ❌ Ошибок: {total_errors}")
    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
    logger.info("=" * 60)
    logger.info("")
    
    # Закрываем подключение
    await unified_db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
