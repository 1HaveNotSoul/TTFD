"""
Leaderboard handler - таблица лидеров
"""
from telegram import Update
from telegram.ext import ContextTypes

from domain.services.user_service import UserService
from domain.models.user import get_rank_by_id


class LeaderboardHandler:
    """Handler для таблицы лидеров"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def handle_leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать команду /leaderboard"""
        try:
            # Получаем топ 10
            top_users = await self.user_service.get_leaderboard(limit=10)
            
            if not top_users:
                await update.message.reply_text("📊 Таблица лидеров пуста")
                return
            
            # Формируем сообщение
            message = "🏆 **Таблица лидеров**\n\n"
            
            medals = ["🥇", "🥈", "🥉"]
            
            for i, user in enumerate(top_users, 1):
                rank = get_rank_by_id(user.rank_id)
                
                # Медали для топ-3
                if i <= 3:
                    prefix = medals[i-1]
                else:
                    prefix = f"{i}."
                
                # Имя пользователя
                name = user.first_name or user.username or "Unknown"
                if len(name) > 15:
                    name = name[:15] + "..."
                
                message += f"{prefix} **{name}**\n"
                message += f"   🎭 {rank.name} | ⭐ {user.xp} XP\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
        except Exception as e:
            print(f"❌ Ошибка в leaderboard_handler: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуй позже.")
