"""
Daily reward handler - обработчик ежедневной награды
"""
from telegram import Update
from telegram.ext import ContextTypes

from domain.services.user_service import UserService
from core.exceptions import CooldownError


class DailyHandler:
    """Handler для ежедневной награды"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def handle_daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать команду /daily"""
        user_tg = update.effective_user
        
        try:
            # Получаем или создаём пользователя
            user = await self.user_service.get_or_create_user(
                str(user_tg.id),
                user_tg.username or 'Unknown',
                user_tg.first_name or ''
            )
            
            # Пытаемся получить награду
            result = await self.user_service.claim_daily(str(user_tg.id))
            
            # Формируем сообщение
            message = f"""
🎁 **Ежедневная награда получена!**

⭐ +{result['xp']} XP
💰 +{result['coins']} монет
"""
            
            # Если был ранк-ап
            if result['rank_up']:
                new_rank = result['new_rank']
                message += f"\n🎉 **ПОВЫШЕНИЕ РАНГА!**\n"
                message += f"🎭 Новый ранг: **{new_rank.name}**\n"
                message += f"🎁 Награда: +{new_rank.reward_coins} монет"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        
        except CooldownError as e:
            await update.message.reply_text(f"⏱️ {str(e)}")
        
        except Exception as e:
            print(f"❌ Ошибка в daily_handler: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуй позже.")
