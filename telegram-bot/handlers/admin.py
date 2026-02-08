"""
Админ команды
"""

from telegram import Update
from telegram.ext import ContextTypes
from database import db
from config import TELEGRAM_ADMIN_IDS

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /admin - админ-панель"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    if telegram_id not in TELEGRAM_ADMIN_IDS:
        await update.message.reply_text("❌ У тебя нет доступа к админ-панели")
        return
    
    all_users = db.get_all_users()
    global_stats = db.data['global_stats']
    
    text = f"""
⚙️ **Админ-панель**

👥 Всего пользователей: {global_stats['total_users']}
✨ Всего XP заработано: {global_stats['total_xp_earned']}
💰 Всего монет заработано: {global_stats['total_coins_earned']}

Используй команды:
/broadcast <текст> - Рассылка всем пользователям
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /broadcast - рассылка всем пользователям"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    if telegram_id not in TELEGRAM_ADMIN_IDS:
        await update.message.reply_text("❌ У тебя нет доступа к этой команде")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /broadcast <текст сообщения>"
        )
        return
    
    message_text = ' '.join(context.args)
    all_users = db.get_all_users()
    
    success_count = 0
    fail_count = 0
    
    await update.message.reply_text(f"📢 Начинаю рассылку для {len(all_users)} пользователей...")
    
    for db_user in all_users:
        try:
            await context.bot.send_message(
                chat_id=int(db_user['telegram_id']),
                text=f"📢 **Объявление от администрации:**\n\n{message_text}",
                parse_mode='Markdown'
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
    
    await update.message.reply_text(
        f"✅ Рассылка завершена!\n\n"
        f"Успешно: {success_count}\n"
        f"Ошибок: {fail_count}"
    )
