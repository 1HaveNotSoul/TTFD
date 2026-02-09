"""
Команда /code для привязки Discord через код
Код генерируется в Discord боте и используется здесь
"""

from telegram import Update
from telegram.ext import ContextTypes
from database import db
import os
import asyncpg
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /code <КОД> - привязать Discord через код из Discord бота
    
    Использование: /code ABC123
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Проверяем аргументы
    if not context.args or len(context.args) == 0:
        text = """
🔗 **Привязка Discord через код**

**Использование:** `/code <КОД>`

**Пример:** `/code ABC123`

**Как получить код:**
1. Зайди в Discord бот
2. Используй команду `/getcode`
3. Бот отправит код в личные сообщения
4. Используй этот код здесь: `/code <КОД>`

⏰ **Код действителен 3 минуты**
"""
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    code = context.args[0].upper().strip()
    
    # Проверяем формат кода (6 символов, заглавные буквы и цифры)
    if len(code) != 6 or not code.isalnum():
        text = """
❌ **Неправильный формат кода**

Код должен состоять из 6 символов (заглавные буквы и цифры).

**Пример:** `ABC123`

Получи новый код в Discord боте: `/getcode`
"""
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    try:
        # Подключаемся к PostgreSQL
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            text = """
❌ **База данных недоступна**

Система кодов требует подключения к PostgreSQL.
Обратись к администратору.
"""
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        conn = await asyncpg.connect(database_url)
        
        try:
            # Проверяем код в БД
            code_data = await conn.fetchrow("""
                SELECT code, discord_id, used, expires_at, created_at
                FROM link_codes
                WHERE code = $1 AND platform = 'discord'
            """, code)
            
            if not code_data:
                text = """
❌ **Код не найден**

Возможные причины:
• Код неправильный
• Код уже использован
• Код истёк (действителен 3 минуты)

Получи новый код в Discord боте: `/getcode`
"""
                await update.message.reply_text(text, parse_mode='Markdown')
                return
            
            # Проверяем истёк ли код
            if code_data['expires_at'] < datetime.now():
                text = """
❌ **Код истёк**

Коды действительны только 3 минуты.

Получи новый код в Discord боте: `/getcode`
"""
                await update.message.reply_text(text, parse_mode='Markdown')
                return
            
            # Проверяем использован ли код
            if code_data['used']:
                text = """
❌ **Код уже использован**

Каждый код можно использовать только один раз.

Получи новый код в Discord боте: `/getcode`
"""
                await update.message.reply_text(text, parse_mode='Markdown')
                return
            
            discord_id = code_data['discord_id']
            
            # Проверяем не привязан ли уже этот Telegram к другому Discord
            existing_link = db.get_discord_link(telegram_id)
            if existing_link and existing_link != discord_id:
                text = f"""
⚠️ **Telegram уже привязан**

Твой Telegram уже привязан к Discord ID: `{existing_link}`

Хочешь перепривязать к новому Discord?
Используй `/unlink` сначала.
"""
                await update.message.reply_text(text, parse_mode='Markdown')
                return
            
            # Помечаем код как использованный
            await conn.execute("""
                UPDATE link_codes
                SET used = TRUE,
                    used_at = $1,
                    telegram_id = $2
                WHERE code = $3
            """, datetime.now(), telegram_id, code)
            
            # Сохраняем привязку в локальной БД
            db.link_discord(telegram_id, discord_id)
            
            # Получаем данные пользователя
            user_data = db.get_user(telegram_id)
            
            text = f"""
✅ **Аккаунты привязаны!**

**Discord ID:** `{discord_id}`
**Telegram ID:** `{telegram_id}`

📊 **Твои данные:**
💰 Монеты: {user_data.get('coins', 0)}
✨ XP: {user_data.get('xp', 0)}
⭐ Ранг: #{user_data.get('rank_id', 0)}

🎉 **Что дальше?**
Теперь твой баланс синхронизирован между Telegram и Discord!
Зарабатывай монеты на любой платформе - они будут везде одинаковые.
"""
            
            await update.message.reply_text(text, parse_mode='Markdown')
            logger.info(f"✅ Привязка успешна: Telegram {telegram_id} ↔ Discord {discord_id} (код: {code})")
        
        finally:
            await conn.close()
    
    except Exception as e:
        text = f"""
❌ **Ошибка привязки**

{str(e)}

Попробуй позже или обратись к администратору.
"""
        await update.message.reply_text(text, parse_mode='Markdown')
        logger.error(f"❌ Ошибка привязки через код: {e}")
        import traceback
        traceback.print_exc()


async def checklink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /checklink - проверить статус привязки Discord
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Проверяем привязку
    discord_id = db.get_discord_link(telegram_id)
    
    if not discord_id:
        text = """
❌ **Discord не привязан**

Твой Telegram не привязан к Discord аккаунту.

**Как привязать:**
1. Зайди в Discord бот
2. Используй команду `/getcode`
3. Получи код в личные сообщения
4. Используй `/code <КОД>` здесь в Telegram

⏰ **Код действителен 3 минуты**
"""
    else:
        user_data = db.get_user(telegram_id)
        
        text = f"""
✅ **Аккаунты привязаны!**

**📱 Telegram**
ID: `{telegram_id}`
Username: @{user.username or 'не указан'}

**💬 Discord**
ID: `{discord_id}`

**📊 Синхронизированные данные:**
💰 Монеты: {user_data.get('coins', 0)}
✨ XP: {user_data.get('xp', 0)}
⭐ Ранг: #{user_data.get('rank_id', 0)}
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')


async def unlink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /unlink - отвязать Discord аккаунт
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Проверяем привязку
    discord_id = db.get_discord_link(telegram_id)
    
    if not discord_id:
        text = """
❌ **Discord не привязан**

У тебя нет привязанного Discord аккаунта.
"""
        await update.message.reply_text(text, parse_mode='Markdown')
        return
    
    # Отвязываем
    db.unlink_discord(telegram_id)
    
    text = f"""
✅ **Discord отвязан**

Discord ID `{discord_id}` успешно отвязан от твоего Telegram.

Чтобы привязать снова:
1. Используй `/getcode` в Discord боте
2. Используй `/code <КОД>` здесь
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')
    logger.info(f"✅ Отвязка: Telegram {telegram_id} ↔ Discord {discord_id}")
