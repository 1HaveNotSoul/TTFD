"""
Games Menu Handler - главное меню игр
Рефакторинг: использует централизованные callback
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.game_service import GameService
from domain.services.user_service import UserService
from core.callbacks import GameCallback


class GamesMenuHandler:
    """Handler для меню игр"""
    
    def __init__(self, game_service: GameService, user_service: UserService):
        self.game_service = game_service
        self.user_service = user_service
    
    async def handle_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Главное меню игр"""
        query = update.callback_query
        if query:
            await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_or_create_user(
            str(user_tg.id),
            user_tg.username or 'Unknown',
            user_tg.first_name or ''
        )
        
        text = f"""
🎮 **Игры TTFD**

💰 Твой баланс: {user.coins} монет
✨ XP: {user.xp}

Выбери игру:
"""
        
        keyboard = [
            [InlineKeyboardButton("🎲 Угадай число", callback_data=GameCallback.guess_start())],
            [InlineKeyboardButton("🧠 Квиз", callback_data=GameCallback.quiz_start())],
            [InlineKeyboardButton("🎰 Ежедневный спин", callback_data=GameCallback.spin_start())],
            [InlineKeyboardButton("📊 Моя статистика", callback_data=GameCallback.stats())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика игр пользователя"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        stats = await self.game_service.get_user_stats(user.id)
        
        text = f"""
📊 **Твоя игровая статистика**

🎮 Игр сыграно: {stats.total_games}
🏆 Побед: {stats.total_wins}
📉 Поражений: {stats.total_losses}
📈 Процент побед: {stats.win_rate:.1f}%

💰 Всего выиграно: {stats.total_coins_won} монет
💸 Всего проиграно: {stats.total_coins_lost} монет
💵 Чистая прибыль: {stats.net_profit} монет

✨ Всего XP заработано: {stats.total_xp_earned}

**По играм:**
🎲 Угадай число: {stats.guess_games} игр ({stats.guess_wins} побед)
🧠 Квиз: {stats.quiz_games} игр ({stats.quiz_wins} побед)
🎰 Спинов: {stats.spin_count}
"""
        
        keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
