"""
Spin Handler - ежедневный спин
Рефакторинг: использует централизованные callback
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.game_service import GameService
from domain.services.user_service import UserService
from core.exceptions import CooldownError
from core.callbacks import GameCallback


class SpinHandler:
    """Handler для ежедневного спина"""
    
    def __init__(self, game_service: GameService, user_service: UserService):
        self.game_service = game_service
        self.user_service = user_service
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать меню спина"""
        query = update.callback_query
        if query:
            await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_or_create_user(
            str(user_tg.id),
            user_tg.username or 'Unknown',
            user_tg.first_name or ''
        )
        
        # Проверка кулдауна
        can_spin, time_left = await self.game_service.can_spin(user.id)
        
        if not can_spin:
            text = f"""
⏰ **Ежедневный спин**

Ты уже крутил сегодня!
Следующий спин через: {time_left}

Возвращайся завтра! 🌙
"""
            keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if query:
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            else:
                await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        text = """
🎰 **Ежедневный спин**

Крути колесо фортуны и получи награду!
Доступно 1 раз в 24 часа.

Возможные награды:
💰 10-200 монет
💎 50 XP
🎉 ДЖЕКПОТ - 500 монет!
"""
        
        keyboard = [
            [InlineKeyboardButton("🎰 КРУТИТЬ!", callback_data=GameCallback.spin_do())],
            [InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_spin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Крутить спин"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        try:
            # Крутим
            result = await self.game_service.spin_wheel(user)
            
            reward = result['reward']
            
            text = f"""
🎰 **Результат спина!**

🎉 Ты получил: **{reward['name']}**

"""
            
            if result['coins'] > 0:
                text += f"💰 +{result['coins']} монет\n"
            
            if result['xp'] > 0:
                text += f"✨ +{result['xp']} XP\n"
            
            text += "\nВозвращайся завтра за новой наградой! 🌙"
            
            keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        except CooldownError as e:
            await query.answer(str(e), show_alert=True)
            await self.handle_start(update, context)
