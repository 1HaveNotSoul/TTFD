"""
Profile handler - обработчик команды /profile
"""
from telegram import Update
from telegram.ext import ContextTypes

from domain.services.user_service import UserService
from core.exceptions import UserNotFoundError


class ProfileHandler:
    """Handler для профиля пользователя"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def handle_profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать команду /profile"""
        user_tg = update.effective_user
        
        try:
            # Получаем или создаём пользователя
            user = await self.user_service.get_or_create_user(
                str(user_tg.id),
                user_tg.username or 'Unknown',
                user_tg.first_name or ''
            )
            
            # Получаем ранг и прогресс
            rank = await self.user_service.get_user_rank(str(user_tg.id))
            next_rank = await self.user_service.get_next_rank(str(user_tg.id))
            progress = await self.user_service.get_rank_progress(str(user_tg.id))
            
            # Формируем сообщение
            message = f"""
👤 **Профиль {user.first_name}**

🎭 Ранг: **{rank.name}**
⭐ XP: **{user.xp}**
💰 Монеты: **{user.coins}**

📊 Прогресс до следующего ранга:
"""
            
            if next_rank:
                message += f"🎯 {next_rank.name}: {progress['xp_to_next']} XP\n"
                message += f"{'▓' * (progress['progress'] // 10)}{'░' * (10 - progress['progress'] // 10)} {progress['progress']}%"
            else:
                message += "🏆 Максимальный ранг достигнут!"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
        except UserNotFoundError as e:
            await update.message.reply_text(f"❌ {str(e)}")
        except Exception as e:
            print(f"❌ Ошибка в profile_handler: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуй позже.")
