"""
Улучшенная команда /link для привязки Discord аккаунта
Поддерживает unified database и синхронизацию баланса
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
import logging

logger = logging.getLogger(__name__)


async def link_discord_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /link - привязать Discord аккаунт с поддержкой unified database
    
    Использование: /link <discord_id>
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Проверка аргументов
    if not context.args:
        help_text = """
🔗 **Привязка Discord аккаунта**

**Использование:** `/link <discord_id>`

**Пример:** `/link 123456789012345678`

**Как узнать свой Discord ID:**
1. Открой Discord
2. Настройки → Расширенные
3. Включи "Режим разработчика"
4. Нажми ПКМ на свой профиль
5. Выбери "Копировать ID"

После привязки:
✅ Баланс синхронизируется между платформами
✅ Ранги одинаковые везде
✅ Прогресс сохраняется
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
        return
    
    discord_id = context.args[0]
    
    # Валидация Discord ID
    if not discord_id.isdigit():
        await update.message.reply_text(
            "❌ Discord ID должен быть числом!\n\n"
            "Пример: `/link 123456789012345678`",
            parse_mode='Markdown'
        )
        return
    
    if len(discord_id) < 17 or len(discord_id) > 19:
        await update.message.reply_text(
            "❌ Discord ID должен содержать 17-19 цифр!\n\n"
            "Убедись что скопировал правильный ID.",
            parse_mode='Markdown'
        )
        return
    
    # Сохраняем в локальную БД
    db.link_discord(telegram_id, discord_id)
    logger.info(f"Discord ID {discord_id} привязан к Telegram {telegram_id} (локальная БД)")
    
    # Пытаемся синхронизировать с unified database
    try:
        from infrastructure.database.unified_integration import get_unified_integration
        
        unified = await get_unified_integration()
        
        # Получаем пользователя Telegram
        tg_user = await unified.unified_db.get_user_by_telegram(telegram_id)
        
        if not tg_user:
            # Создаём пользователя в unified database
            tg_user = await unified.get_or_create_user(
                telegram_id=telegram_id,
                username=user.username or 'Unknown',
                display_name=user.first_name or 'Unknown'
            )
            logger.info(f"Создан пользователь в unified database: {tg_user.id}")
        
        # Проверяем существует ли Discord пользователь
        discord_user = await unified.unified_db.get_user_by_discord(discord_id)
        
        if discord_user:
            # Discord аккаунт уже существует
            if discord_user.id == tg_user.id:
                # Уже привязан к этому же аккаунту
                text = f"""
✅ **Аккаунты уже привязаны!**

Discord ID: `{discord_id}`

📊 **Твои данные:**
💰 Монеты: {discord_user.coins}
✨ XP: {discord_user.xp}
⭐ Ранг: #{discord_user.rank_id}

Баланс синхронизирован между Telegram и Discord! 🎉
"""
            else:
                # Discord привязан к другому аккаунту
                text = f"""
⚠️ **Discord ID уже используется**

Discord ID `{discord_id}` уже привязан к другому аккаунту.

Если это твой аккаунт, обратись к администратору для объединения аккаунтов.
"""
        else:
            # Discord аккаунт не найден - привязываем ID
            success = await unified.unified_db.link_discord(tg_user.id, discord_id)
            
            if success:
                text = f"""
✅ **Discord ID сохранён!**

Discord ID: `{discord_id}`

⚠️ **Важно:** Discord аккаунт ещё не зарегистрирован в боте.

**Что делать дальше:**
1. Зайди в Discord бот
2. Используй любую команду (например `/profile`)
3. Аккаунты автоматически синхронизируются! 🎉

После этого:
✅ Баланс будет общим
✅ Ранги синхронизируются
✅ Прогресс сохраняется везде
"""
                logger.info(f"Discord ID {discord_id} привязан к unified user {tg_user.id}")
            else:
                text = f"""
❌ **Ошибка привязки**

Не удалось привязать Discord ID к unified database.
Discord ID сохранён локально.

Попробуй позже или обратись к администратору.
"""
        
    except ImportError:
        # Unified integration не установлена
        text = f"""
✅ **Discord ID сохранён!**

Discord ID: `{discord_id}`

⚠️ Unified database не настроена.
Привязка сохранена локально.

Для полной синхронизации баланса между платформами
обратись к администратору.
"""
        logger.warning("Unified integration не доступна")
    
    except Exception as e:
        # Другая ошибка
        text = f"""
✅ **Discord ID сохранён!**

Discord ID: `{discord_id}`

⚠️ Ошибка синхронизации с unified database: {str(e)}
Привязка сохранена локально.

Попробуй позже или обратись к администратору.
"""
        logger.error(f"Ошибка привязки Discord: {e}")
    
    # Кнопка назад
    keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def unlink_discord_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /unlink - отвязать Discord аккаунт (только для админов)
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Проверка прав админа
    from config import TELEGRAM_ADMIN_IDS
    if telegram_id not in TELEGRAM_ADMIN_IDS:
        await update.message.reply_text(
            "❌ Эта команда доступна только администраторам!"
        )
        return
    
    db_user = db.get_user(telegram_id)
    
    if not db_user.get('discord_id'):
        await update.message.reply_text("❌ Discord аккаунт не привязан!")
        return
    
    # Отвязываем локально
    db.update_user(telegram_id, discord_id=None)
    
    text = """
✅ **Discord аккаунт отвязан!**

⚠️ Обрати внимание:
• Локальная привязка удалена
• Unified database может сохранить связь
• Для полного удаления обратись к администратору
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def check_link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /checklink - проверить статус привязки
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    db_user = db.get_user(telegram_id)
    
    if not db_user.get('discord_id'):
        text = """
❌ **Discord аккаунт не привязан**

Используй `/link <discord_id>` для привязки.

Пример: `/link 123456789012345678`
"""
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    discord_id = db_user['discord_id']
    
    # Проверяем unified database
    try:
        from infrastructure.database.unified_integration import get_unified_integration
        
        unified = await get_unified_integration()
        tg_user = await unified.unified_db.get_user_by_telegram(telegram_id)
        
        if tg_user and tg_user.discord_id:
            # Проверяем Discord пользователя
            discord_user = await unified.unified_db.get_user_by_discord(discord_id)
            
            if discord_user:
                text = f"""
✅ **Аккаунты привязаны и синхронизированы!**

**Telegram:**
• ID: `{telegram_id}`
• Username: @{user.username or 'Unknown'}

**Discord:**
• ID: `{discord_id}`
• Username: {discord_user.username}

**Unified данные:**
💰 Монеты: {tg_user.coins}
✨ XP: {tg_user.xp}
⭐ Ранг: #{tg_user.rank_id}

🎉 Баланс синхронизирован между платформами!
"""
            else:
                text = f"""
⚠️ **Частичная привязка**

**Telegram:** `{telegram_id}` ✅
**Discord:** `{discord_id}` ⚠️

Discord аккаунт не найден в unified database.
Зайди в Discord бот для завершения привязки.
"""
        else:
            text = f"""
⚠️ **Локальная привязка**

Discord ID: `{discord_id}`

Привязка сохранена локально, но не синхронизирована
с unified database.

Для полной синхронизации обратись к администратору.
"""
    
    except Exception as e:
        text = f"""
⚠️ **Локальная привязка**

Discord ID: `{discord_id}`

Unified database недоступна.
Привязка работает только локально.
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
