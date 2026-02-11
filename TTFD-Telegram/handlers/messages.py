"""
Обработчик текстовых сообщений
"""

from telegram import Update
from telegram.ext import ContextTypes
from utils.tickets import create_ticket

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    telegram_id = str(user.id)
    text = update.message.text
    
    # Проверяем ожидание тикета
    if context.user_data.get('waiting_for_ticket'):
        # Создаём тикет
        ticket_id = create_ticket(
            telegram_id=telegram_id,
            user_name=user.first_name,
            username=user.username or 'Unknown',
            message=text,
            category='Общий'
        )
        
        context.user_data['waiting_for_ticket'] = False
        
        await update.message.reply_text(
            f"✅ Тикет #{ticket_id} создан!\n\nМы ответим тебе в ближайшее время."
        )
        return
    
    # Обычное сообщение
    await update.message.reply_text(
        "Используй /start для открытия главного меню или /help для справки."
    )
