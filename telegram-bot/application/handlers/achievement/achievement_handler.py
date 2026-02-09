"""
Achievement Handler - обработка команд достижений
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

from domain.services.achievement_service import AchievementService
from domain.services.user_service import UserService

logger = logging.getLogger(__name__)


class AchievementHandler:
    """Handler для достижений"""
    
    def __init__(
        self,
        achievement_service: AchievementService,
        user_service: UserService
    ):
        self.achievement_service = achievement_service
        self.user_service = user_service
    
    async def handle_achievements_command(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Команда /achievements - показать меню достижений"""
        user_id = update.effective_user.id
        
        # Получаем или создаём пользователя
        user = await self.user_service.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name
        )
        
        # Получаем статистику
        stats = await self.achievement_service.get_user_stats(user_id)
        
        # Получаем незабранные награды
        unclaimed = await self.achievement_service.get_unclaimed_achievements(user_id)
        
        text = (
            f"🏆 <b>Достижения</b>\n\n"
            f"📊 Прогресс:\n"
            f"• Получено: {stats['completed']}\n"
            f"• В процессе: {stats['in_progress']}\n"
            f"• Завершено: {stats['completion_percent']:.1f}%\n"
        )
        
        if unclaimed:
            text += f"\n🎁 Незабранных наград: {len(unclaimed)}"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Все достижения", callback_data="ach_list_all"),
                InlineKeyboardButton("✅ Полученные", callback_data="ach_list_completed")
            ],
            [
                InlineKeyboardButton("🎮 Игры", callback_data="ach_cat_games"),
                InlineKeyboardButton("⚡ Активность", callback_data="ach_cat_activity")
            ],
            [
                InlineKeyboardButton("🔥 Стрики", callback_data="ach_cat_streak"),
                InlineKeyboardButton("🏆 Сезоны", callback_data="ach_cat_season")
            ]
        ]
        
        if unclaimed:
            keyboard.insert(0, [
                InlineKeyboardButton(
                    f"🎁 Забрать награды ({len(unclaimed)})",
                    callback_data="ach_claim_all"
                )
            ])
        
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
    
    async def handle_list_all(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Показать все достижения"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        # Получаем все достижения с прогрессом
        achievements = await self.achievement_service.get_user_achievements(user_id)
        
        if not achievements:
            # Если нет прогресса - показываем все доступные
            all_achievements = await self.achievement_service.get_all_achievements()
            text = "🏆 <b>Все достижения</b>\n\n"
            
            for ach in all_achievements[:10]:  # Первые 10
                text += (
                    f"{ach.icon} <b>{ach.name}</b>\n"
                    f"   {ach.description}\n"
                    f"   {self.achievement_service.format_rarity(ach.rarity)}\n"
                    f"   Награда: {ach.reward_xp} XP, {ach.reward_coins} монет\n\n"
                )
            
            if len(all_achievements) > 10:
                text += f"... и ещё {len(all_achievements) - 10} достижений"
        else:
            text = "🏆 <b>Твои достижения</b>\n\n"
            
            for progress, ach in achievements[:10]:
                status = "✅" if progress.is_completed else "⏳"
                percent = progress.progress_percent
                
                text += (
                    f"{status} {ach.icon} <b>{ach.name}</b>\n"
                    f"   {ach.description}\n"
                    f"   Прогресс: {progress.current_progress}/{progress.required_progress} ({percent:.0f}%)\n"
                )
                
                if progress.is_completed:
                    text += f"   ✅ Получено\n"
                
                text += "\n"
            
            if len(achievements) > 10:
                text += f"... и ещё {len(achievements) - 10} достижений"
        
        keyboard = [[
            InlineKeyboardButton("◀️ Назад", callback_data="ach_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_list_completed(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Показать полученные достижения"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        
        completed = await self.achievement_service.get_completed_achievements(user_id)
        
        if not completed:
            text = "🏆 <b>Полученные достижения</b>\n\n"
            text += "У тебя пока нет полученных достижений.\n"
            text += "Играй в игры, будь активным и получай награды!"
        else:
            text = f"🏆 <b>Полученные достижения ({len(completed)})</b>\n\n"
            
            for progress, ach in completed[:15]:
                text += (
                    f"✅ {ach.icon} <b>{ach.name}</b>\n"
                    f"   {ach.description}\n"
                    f"   {self.achievement_service.format_rarity(ach.rarity)}\n"
                    f"   Награда: {ach.reward_xp} XP, {ach.reward_coins} монет\n\n"
                )
            
            if len(completed) > 15:
                text += f"... и ещё {len(completed) - 15} достижений"
        
        keyboard = [[
            InlineKeyboardButton("◀️ Назад", callback_data="ach_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_category(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Показать достижения по категории"""
        query = update.callback_query
        await query.answer()
        
        # Извлекаем категорию из callback_data
        category = query.data.replace("ach_cat_", "")
        
        user_id = update.effective_user.id
        
        # Получаем все достижения категории
        all_achievements = await self.achievement_service.get_all_achievements(
            category=category
        )
        
        # Получаем прогресс пользователя
        user_achievements = await self.achievement_service.get_user_achievements(user_id)
        user_progress_map = {
            progress.achievement_id: progress
            for progress, _ in user_achievements
        }
        
        category_name = self.achievement_service.format_category(category)
        text = f"{category_name}\n\n"
        
        for ach in all_achievements:
            progress = user_progress_map.get(ach.id)
            
            if progress:
                status = "✅" if progress.is_completed else "⏳"
                percent = progress.progress_percent
                text += (
                    f"{status} {ach.icon} <b>{ach.name}</b>\n"
                    f"   {ach.description}\n"
                    f"   Прогресс: {progress.current_progress}/{progress.required_progress} ({percent:.0f}%)\n\n"
                )
            else:
                text += (
                    f"⏳ {ach.icon} <b>{ach.name}</b>\n"
                    f"   {ach.description}\n"
                    f"   Прогресс: 0/{ach.requirement_value} (0%)\n\n"
                )
        
        keyboard = [[
            InlineKeyboardButton("◀️ Назад", callback_data="ach_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    async def handle_claim_all(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Забрать все незабранные награды"""
        query = update.callback_query
        await query.answer("🎁 Награды получены!")
        
        user_id = update.effective_user.id
        
        # Получаем незабранные достижения
        unclaimed = await self.achievement_service.get_unclaimed_achievements(user_id)
        
        if not unclaimed:
            await query.edit_message_text(
                "У тебя нет незабранных наград!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Назад", callback_data="ach_menu")
                ]])
            )
            return
        
        total_xp = sum(ach.reward_xp for _, ach in unclaimed)
        total_coins = sum(ach.reward_coins for _, ach in unclaimed)
        
        text = f"🎁 <b>Награды получены!</b>\n\n"
        
        for progress, ach in unclaimed:
            text += (
                f"✅ {ach.icon} <b>{ach.name}</b>\n"
                f"   +{ach.reward_xp} XP, +{ach.reward_coins} монет\n\n"
            )
        
        text += f"\n💰 <b>Итого:</b>\n"
        text += f"• XP: +{total_xp}\n"
        text += f"• Монеты: +{total_coins}"
        
        keyboard = [[
            InlineKeyboardButton("◀️ К достижениям", callback_data="ach_menu")
        ]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
