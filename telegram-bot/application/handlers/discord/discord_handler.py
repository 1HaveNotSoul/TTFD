"""
Discord Handler - обработка команд Discord интеграции
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Optional
import logging

from domain.services.discord_service import DiscordService
from domain.services.user_service import UserService

logger = logging.getLogger(__name__)


class DiscordHandler:
    """Handler для Discord интеграции"""
    
    def __init__(
        self,
        discord_service: DiscordService,
        user_service: UserService
    ):
        self.discord_service = discord_service
        self.user_service = user_service
    
    async def handle_discord_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Команда /discord - показать меню Discord"""
        user_id = update.effective_user.id
        
        # Получаем или создаём пользователя
        user = await self.user_service.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name
        )
        
        # Проверяем привязку
        link = await self.discord_service.get_active_link(user_id)
        
        if link and link.is_active:
            # Уже привязан
            text = (
                f"🔗 <b>Discord интеграция</b>\n\n"
                f"✅ Твой аккаунт привязан к Discord!\n"
                f"Discord ID: <code>{link.discord_user_id}</code>\n\n"
                f"Роли Discord выдаются автоматически за:\n"
                f"• Достижения (9 ролей)\n"
                f"• Сезонные результаты (топ-10, чемпион)\n"
                f"• Ранги пользователя\n"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🎁 Мои роли", callback_data="discord_roles"),
                    InlineKeyboardButton("📊 Статус", callback_data="discord_status")
                ],
                [
                    InlineKeyboardButton("🔓 Отвязать", callback_data="discord_unlink")
                ]
            ]
        else:
            # Не привязан
            text = (
                f"🔗 <b>Discord интеграция</b>\n\n"
                f"Привяжи свой Discord аккаунт чтобы получать роли за:\n"
                f"• 🏅 Достижения (9 ролей)\n"
                f"• 🏆 Сезонные результаты\n"
                f"• ⭐ Ранги пользователя\n\n"
                f"Роли выдаются автоматически!"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("🔗 Привязать Discord", callback_data="discord_link_start")
                ],
                [
                    InlineKeyboardButton("❓ Как это работает", callback_data="discord_help")
                ]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def handle_link_start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Начать привязку Discord"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Создаём запрос на привязку
        link = await self.discord_service.create_link_request(user_id)
        
        text = (
            f"🔗 <b>Привязка Discord</b>\n\n"
            f"Твой код подтверждения:\n"
            f"<code>{link.verification_code}</code>\n\n"
            f"<b>Как привязать:</b>\n"
            f"1. Зайди на Discord сервер TTFD\n"
            f"2. Напиши команду: <code>/link {link.verification_code}</code>\n"
            f"3. Бот подтвердит привязку\n\n"
            f"⏰ Код действителен 15 минут"
        )
        
        keyboard = [[
            InlineKeyboardButton("◀️ Назад", callback_data="discord_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_unlink(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Отвязать Discord"""
        query = update.callback_query
        await query.answer("🔓 Привязка отозвана")
        
        user_id = update.effective_user.id
        
        await self.discord_service.revoke_link(user_id)
        
        text = (
            f"🔓 <b>Привязка отозвана</b>\n\n"
            f"Твой Discord аккаунт отвязан.\n"
            f"Роли останутся на сервере, но новые выдаваться не будут.\n\n"
            f"Ты можешь привязать аккаунт заново в любое время."
        )
        
        keyboard = [[
            InlineKeyboardButton("◀️ К Discord", callback_data="discord_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_roles(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Показать роли пользователя"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Получаем роли
        grants = await self.discord_service.get_user_role_grants(
            user_id,
            granted_only=True
        )
        
        if not grants:
            text = (
                f"🎁 <b>Мои Discord роли</b>\n\n"
                f"У тебя пока нет выданных ролей.\n"
                f"Получай достижения и участвуй в сезонах!"
            )
        else:
            text = f"🎁 <b>Мои Discord роли ({len(grants)})</b>\n\n"
            
            for grant in grants:
                reason = self._format_reason(grant.reason_type, grant.reason_id)
                text += f"✅ <b>{grant.role_name}</b>\n   {reason}\n\n"
        
        keyboard = [[
            InlineKeyboardButton("◀️ Назад", callback_data="discord_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_status(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Показать статус интеграции"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Получаем привязку
        link = await self.discord_service.get_active_link(user_id)
        
        # Получаем роли
        all_grants = await self.discord_service.get_user_role_grants(user_id)
        granted = [g for g in all_grants if g.is_granted]
        pending = [g for g in all_grants if not g.is_granted]
        
        text = f"📊 <b>Статус Discord интеграции</b>\n\n"
        
        if link and link.is_active:
            text += f"✅ Привязка активна\n"
            text += f"Discord ID: <code>{link.discord_user_id}</code>\n\n"
        else:
            text += f"❌ Привязка не активна\n\n"
        
        text += f"🎁 <b>Роли:</b>\n"
        text += f"• Выдано: {len(granted)}\n"
        
        if pending:
            text += f"• В очереди: {len(pending)}\n"
        
        keyboard = [[
            InlineKeyboardButton("◀️ Назад", callback_data="discord_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_help(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Показать помощь"""
        query = update.callback_query
        await query.answer()
        
        text = (
            f"❓ <b>Как работает Discord интеграция</b>\n\n"
            f"<b>1. Привязка аккаунта:</b>\n"
            f"• Получи код в Telegram боте\n"
            f"• Введи код на Discord сервере\n"
            f"• Аккаунты привязаны!\n\n"
            f"<b>2. Автоматическая выдача ролей:</b>\n"
            f"• За достижения (9 ролей)\n"
            f"• За топ позиции в сезоне\n"
            f"• За ранги пользователя\n\n"
            f"<b>3. Безопасность:</b>\n"
            f"• Один Telegram = один Discord\n"
            f"• Роли не дублируются\n"
            f"• Можно отвязать в любой момент\n\n"
            f"<b>Доступные роли:</b>\n"
            f"• achievement_pro (50 побед)\n"
            f"• achievement_master (100 побед)\n"
            f"• achievement_legend (500 побед)\n"
            f"• achievement_dedicated (500 игр)\n"
            f"• achievement_streak7 (7 дней подряд)\n"
            f"• achievement_streak30 (30 дней подряд)\n"
            f"• achievement_season_top10 (топ-10 сезона)\n"
            f"• achievement_season_champion (чемпион)\n"
            f"• achievement_erudite (10 квизов подряд)"
        )
        
        keyboard = [[
            InlineKeyboardButton("◀️ Назад", callback_data="discord_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    def _format_reason(reason_type: str, reason_id: Optional[str]) -> str:
        """Форматировать причину выдачи роли"""
        if reason_type == "achievement":
            return f"За достижение: {reason_id}"
        elif reason_type == "season_reward":
            return f"За сезон #{reason_id}"
        elif reason_type == "rank":
            return f"За ранг: {reason_id}"
        else:
            return reason_type
