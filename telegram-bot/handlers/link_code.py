"""
Команды привязки через код для Telegram бота
Быстрая привязка Discord аккаунта через одноразовый код
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
import sys
import os
import logging

# Добавляем путь к shared модулю
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

logger = logging.getLogger(__name__)


async def linkcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /linkcode - сгенерировать код для привязки Discord
    
    Использование: /linkcode
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    try:
        from link_codes import get_link_code_manager
        
        # Получаем менеджер кодов
        manager = await get_link_code_manager()
        
        # Генерируем код (действителен 10 минут)
        code = await manager.create_code(telegram_id, platform='telegram', expires_minutes=10)
        
        text = f"""
🔗 **Код для привязки Discord**

**Твой код:** `{code}`

**Как использовать:**
1. Зайди в Discord бот
2. Используй команду `/link {code}`
3. Аккаунты автоматически привяжутся! 🎉

⏰ **Код действителен 10 минут**

После привязки:
✅ Баланс синхронизируется
✅ Ранги одинаковые везде
✅ Прогресс сохраняется
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Сгенерировать новый код", callback_data="linkcode_new")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Код {code} сгенерирован для Telegram {telegram_id}")
    
    except ImportError:
        text = """
❌ **Система кодов недоступна**

Link codes модуль не установлен.
Используй `/link <discord_id>` для привязки.
"""
        await update.message.reply_text(text, parse_mode='Markdown')
    
    except Exception as e:
        text = f"""
❌ **Ошибка генерации кода**

{str(e)}

Попробуй позже или используй `/link <discord_id>`
"""
        await update.message.reply_text(text, parse_mode='Markdown')
        logger.error(f"❌ Ошибка генерации кода: {e}")


async def linkcode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки генерации нового кода"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    
    try:
        from link_codes import get_link_code_manager
        
        manager = await get_link_code_manager()
        code = await manager.create_code(telegram_id, platform='telegram', expires_minutes=10)
        
        text = f"""
🔗 **Новый код для привязки Discord**

**Твой код:** `{code}`

**Как использовать:**
1. Зайди в Discord бот
2. Используй команду `/link {code}`
3. Аккаунты автоматически привяжутся! 🎉

⏰ **Код действителен 10 минут**
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Сгенерировать новый код", callback_data="linkcode_new")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"✅ Новый код {code} сгенерирован для Telegram {telegram_id}")
    
    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            parse_mode='Markdown'
        )
        logger.error(f"❌ Ошибка генерации кода: {e}")


async def mycodes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /mycodes - показать мои коды привязки
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    try:
        from link_codes import get_link_code_manager
        
        manager = await get_link_code_manager()
        codes = await manager.get_user_codes(telegram_id)
        
        if not codes:
            text = """
📭 **У тебя нет кодов привязки**

Используй `/linkcode` чтобы создать новый код.
"""
        else:
            text = "🔗 **Твои коды привязки:**\n\n"
            
            for code_data in codes:
                status = "✅ Использован" if code_data['used'] else "⏰ Активен"
                
                # Проверяем истёк ли код
                from datetime import datetime
                if not code_data['used'] and code_data['expires_at'] < datetime.now():
                    status = "❌ Истёк"
                
                text += f"**{code_data['code']}** - {status}\n"
                
                if code_data['used']:
                    text += f"   Discord ID: `{code_data['discord_id']}`\n"
                else:
                    expires = code_data['expires_at'].strftime('%H:%M')
                    text += f"   Истекает в: {expires}\n"
                
                text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Создать новый код", callback_data="linkcode_new")],
            [InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    except Exception as e:
        text = f"❌ Ошибка: {str(e)}"
        await update.message.reply_text(text, parse_mode='Markdown')
        logger.error(f"❌ Ошибка получения кодов: {e}")
