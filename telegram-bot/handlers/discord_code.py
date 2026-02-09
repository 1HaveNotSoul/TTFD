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
    УПРОЩЁННАЯ ВЕРСИЯ - читает коды из Discord JSON БД
    
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
        # Подключаемся к PostgreSQL БД Discord бота
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            text = """
❌ **Discord БД недоступна**

DATABASE_URL не настроен.
Обратись к администратору.
"""
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        # Исправляем URL для psycopg2
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Подключаемся к БД
        import psycopg2
        from psycopg2.extras import RealDictCursor
        import json
        
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Ищем код в game_stats пользователей
        cur.execute("SELECT id, game_stats FROM users")
        users = cur.fetchall()
        
        discord_id = None
        code_data = None
        
        for user in users:
            game_stats = user.get('game_stats', {})
            if isinstance(game_stats, str):
                game_stats = json.loads(game_stats)
            
            link_code = game_stats.get('link_code')
            if not link_code:
                continue
            
            # Проверяем код
            if link_code.get('code') == code:
                discord_id = user['id']
                code_data = link_code
                break
        
        cur.close()
        conn.close()
        
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
        from datetime import datetime
        expires_at = datetime.fromisoformat(code_data['expires_at'])
        if expires_at < datetime.now():
            text = """
❌ **Код истёк**

Коды действительны только 3 минуты.

Получи новый код в Discord боте: `/getcode`
"""
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        # Проверяем использован ли код
        if code_data.get('used'):
            text = """
❌ **Код уже использован**

Каждый код можно использовать только один раз.

Получи новый код в Discord боте: `/getcode`
"""
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
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
        
        # Помечаем код как использованный в PostgreSQL БД
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Обновляем game_stats
        cur.execute("SELECT game_stats FROM users WHERE id = %s", (discord_id,))
        result = cur.fetchone()
        
        if result:
            game_stats = result['game_stats']
            if isinstance(game_stats, str):
                game_stats = json.loads(game_stats)
            
            # Помечаем код как использованный
            if 'link_code' in game_stats:
                game_stats['link_code']['used'] = True
                game_stats['link_code']['used_at'] = datetime.now().isoformat()
                game_stats['link_code']['telegram_id'] = telegram_id
            
            # Сохраняем обратно
            cur.execute(
                "UPDATE users SET game_stats = %s WHERE id = %s",
                (json.dumps(game_stats), discord_id)
            )
            
            # Добавляем telegram_id в users таблицу
            cur.execute(
                "UPDATE users SET telegram_id = %s WHERE id = %s",
                (telegram_id, discord_id)
            )
            
            conn.commit()
        
        cur.close()
        conn.close()
        
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
    
    except Exception as e:
        text = f"❌ Ошибка привязки\n\n{str(e)}\n\nПопробуй позже или обратись к администратору."
        await update.message.reply_text(text)
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
