"""
Season Handler - просмотр сезона и рейтинга
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.season_service import SeasonService
from domain.services.user_service import UserService
from core.callbacks import MenuCallback


class SeasonHandler:
    """Handler для сезонов"""
    
    def __init__(
        self,
        season_service: SeasonService,
        user_service: UserService
    ):
        self.season_service = season_service
        self.user_service = user_service
    
    async def handle_season_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о текущем сезоне"""
        query = update.callback_query
        if query:
            await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_or_create_user(
            str(user_tg.id),
            user_tg.username or 'Unknown',
            user_tg.first_name or ''
        )
        
        # Получаем активный сезон
        season = await self.season_service.get_or_create_active_season()
        
        # Получаем прогресс пользователя
        progress = await self.season_service.get_user_progress(user.id)
        
        # Получаем статистику сезона
        stats = await self.season_service.get_season_stats()
        
        text = f"""
🏆 **{season.name}**

⏰ Осталось: **{season.days_left} дней**
📅 Завершится: {season.end_date.strftime('%d.%m.%Y')}

**Твой прогресс:**
✨ Сезонный XP: {progress.season_xp}
💰 Сезонные монеты: {progress.season_coins}
🎮 Игр сыграно: {progress.games_played}
🏆 Побед: {progress.games_won} ({progress.win_rate:.1f}%)

🔥 Текущий стрик: {progress.current_streak} дней
⭐ Лучший стрик: {progress.best_streak} дней

📊 Твоя позиция: #{progress.rank if progress.rank else '—'}

**Статистика сезона:**
👥 Участников: {stats['total_players']}
🎮 Игр сыграно: {stats['total_games']}
"""
        
        keyboard = [
            [InlineKeyboardButton("🏆 Рейтинг сезона", callback_data="season_leaderboard")],
            [InlineKeyboardButton("🎁 Награды", callback_data="season_rewards")],
            [InlineKeyboardButton("🔙 Назад", callback_data=MenuCallback.main())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Рейтинг сезона"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        # Получаем сезон
        season = await self.season_service.get_or_create_active_season()
        
        # Получаем топ-20
        leaderboard = await self.season_service.get_season_leaderboard(limit=20)
        
        # Получаем позицию пользователя
        user_progress = await self.season_service.get_user_progress(user.id)
        
        text = f"🏆 **Рейтинг {season.name}**\n\n"
        
        for i, (progress, username, first_name) in enumerate(leaderboard, 1):
            medal = ""
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            # Подсвечиваем текущего пользователя
            if progress.user_id == user.id:
                text += f"**{medal} {first_name}: {progress.season_xp} XP** ⬅️\n"
            else:
                text += f"{medal} {first_name}: {progress.season_xp} XP\n"
        
        # Если пользователь не в топ-20
        if user_progress.rank and user_progress.rank > 20:
            text += f"\n...\n**#{user_progress.rank} Ты: {user_progress.season_xp} XP** ⬅️\n"
        
        text += f"\n⏰ До конца сезона: {season.days_left} дней"
        
        keyboard = [
            [InlineKeyboardButton("🔙 К сезону", callback_data="season_info")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data=MenuCallback.main())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_rewards(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о наградах"""
        query = update.callback_query
        await query.answer()
        
        season = await self.season_service.get_or_create_active_season()
        
        text = f"""
🎁 **Награды {season.name}**

Награды выдаются в конце сезона по итоговой позиции в рейтинге:

🥇 **1 место:**
• 5000 XP
• 1000 монет
• Discord роль "Чемпион сезона"
• Титул "🏆 Чемпион сезона"

🥈 **2-3 место:**
• 3000 XP
• 500 монет
• Discord роль "Топ-3 сезона"
• Титул "🥈 Топ-3 сезона"

🥉 **4-10 место:**
• 2000 XP
• 300 монет
• Discord роль "Топ-10 сезона"
• Титул "🥉 Топ-10 сезона"

⭐ **11-50 место:**
• 1000 XP
• 150 монет
• Титул "⭐ Топ-50 сезона"

💡 Играй больше, зарабатывай XP и поднимайся в рейтинге!
"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 К сезону", callback_data="season_info")],
            [InlineKeyboardButton("🏠 Главное меню", callback_data=MenuCallback.main())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
