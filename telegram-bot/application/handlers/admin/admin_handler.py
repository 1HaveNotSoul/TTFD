"""
Admin handler - админ-панель
Рефакторинг: использует централизованные callback и state_manager
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.user_service import UserService
from domain.services.permission_service import PermissionService
from domain.models.permission import Permission, Role
from core.callbacks import AdminCallback
from core.state_manager import state_manager, StateKey, StateTimeout


class AdminHandler:
    """Handler для админ-панели"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.user_repo = user_service.user_repo  # Для доступа к методам репозитория
    
    @PermissionService.require_admin_id()
    async def handle_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработать команду /admin"""
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        # Получаем статистику
        total_users = await self.user_repo.count()
        
        text = f"""
🔧 **Админ-панель**

👤 Твоя роль: **{user.role}**

📊 Статистика:
• Всего пользователей: {total_users}

Выбери действие:
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data=AdminCallback.stats())],
            [InlineKeyboardButton("👥 Пользователи", callback_data=AdminCallback.users())],
            [InlineKeyboardButton("🗄️ Просмотр БД", callback_data=AdminCallback.database())],
            [InlineKeyboardButton("🎫 Тикеты", callback_data=AdminCallback.tickets())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Вернуться в главную админ-панель (callback)"""
        query = update.callback_query
        user_tg = update.effective_user
        
        # Проверяем admin ID для callback тоже
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        user = await self.user_service.get_user(str(user_tg.id))
        total_users = await self.user_repo.count()
        
        text = f"""
🔧 **Админ-панель**

👤 Твоя роль: **{user.role}**

📊 Статистика:
• Всего пользователей: {total_users}

Выбери действие:
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data=AdminCallback.stats())],
            [InlineKeyboardButton("👥 Пользователи", callback_data=AdminCallback.users())],
            [InlineKeyboardButton("🗄️ Просмотр БД", callback_data=AdminCallback.database())],
            [InlineKeyboardButton("🎫 Тикеты", callback_data=AdminCallback.tickets())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @PermissionService.require_permission(Permission.VIEW_ANALYTICS)
    async def handle_stats_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель статистики (callback)"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        # Получаем статистику из БД
        total_users = await self.user_service.user_repo.count()
        leaderboard = await self.user_service.get_leaderboard(limit=3)
        
        text = f"""
📊 **Статистика платформы**

👥 Пользователи: {total_users}

🏆 Топ-3:
"""
        
        for i, user in enumerate(leaderboard, 1):
            text += f"{i}. {user.first_name}: {user.xp} XP\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data=AdminCallback.panel())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @PermissionService.require_permission(Permission.MANAGE_USERS)
    async def handle_users_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель управления пользователями (callback)"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        # Получаем последних пользователей
        all_users = await self.user_service.user_repo.get_all()
        recent_users = sorted(all_users, key=lambda u: u.created_at, reverse=True)[:5]
        
        text = f"""
👥 **Управление пользователями**

Всего пользователей: {len(all_users)}

Последние 5 пользователей:
"""
        
        for user in recent_users:
            text += f"• {user.first_name} (@{user.username or 'нет'}) - {user.xp} XP\n"
        
        text += "\n💡 Используй команды:\n"
        text += "• /setrole <telegram_id> <role> - изменить роль\n"
        text += "• /broadcast <текст> - рассылка\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Админ-панель", callback_data=AdminCallback.panel())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @PermissionService.require_permission(Permission.MANAGE_USERS)
    async def handle_set_role_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Изменить роль пользователя"""
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await update.message.reply_text("❌ У тебя нет доступа к этой команде")
            return
        
        # Формат: /setrole @username role
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Использование: /setrole <telegram_id> <role>\n"
                "Роли: user, vip, moderator, admin"
            )
            return
        
        target_id = context.args[0]
        new_role = context.args[1].lower()
        
        # Валидация роли
        valid_roles = ['user', 'vip', 'moderator', 'admin']
        if new_role not in valid_roles:
            await update.message.reply_text(f"❌ Неверная роль. Доступные: {', '.join(valid_roles)}")
            return
        
        try:
            # Получаем пользователя
            target_user = await self.user_service.get_user(target_id)
            
            # Обновляем роль
            target_user.role = new_role
            await self.user_service.user_repo.update(target_user)
            
            await update.message.reply_text(
                f"✅ Роль пользователя {target_user.first_name} изменена на **{new_role}**",
                parse_mode='Markdown'
            )
        
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    @PermissionService.require_permission(Permission.BROADCAST)
    async def handle_broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Рассылка всем пользователям"""
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await update.message.reply_text("❌ У тебя нет доступа к этой команде")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /broadcast <текст сообщения>")
            return
        
        message_text = ' '.join(context.args)
        
        # Получаем всех пользователей
        all_users = await self.user_service.user_repo.get_all()
        
        sent = 0
        failed = 0
        
        await update.message.reply_text(f"📢 Начинаю рассылку для {len(all_users)} пользователей...")
        
        for user in all_users:
            try:
                await context.bot.send_message(
                    chat_id=int(user.telegram_id),
                    text=f"📢 **Объявление от администрации:**\n\n{message_text}",
                    parse_mode='Markdown'
                )
                sent += 1
            except Exception as e:
                failed += 1
                print(f"Не удалось отправить {user.telegram_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Рассылка завершена!\n"
            f"• Отправлено: {sent}\n"
            f"• Ошибок: {failed}"
        )
    
    @PermissionService.require_permission(Permission.VIEW_ANALYTICS)
    async def handle_database_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель просмотра БД (callback)"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        text = """
🗄️ **Просмотр базы данных**

Выбери таблицу для просмотра:
"""
        
        keyboard = [
            [InlineKeyboardButton("👥 Users (Пользователи)", callback_data=AdminCallback.db_table("users", 0))],
            [InlineKeyboardButton("🎮 Game History (История игр)", callback_data=AdminCallback.db_table("game_history", 0))],
            [InlineKeyboardButton("🎫 Tickets (Тикеты)", callback_data=AdminCallback.db_table("tickets", 0))],
            [InlineKeyboardButton("🏆 Achievements (Достижения)", callback_data=AdminCallback.db_table("achievements", 0))],
            [InlineKeyboardButton("🔙 Админ-панель", callback_data=AdminCallback.panel())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    @PermissionService.require_permission(Permission.VIEW_ANALYTICS)
    async def handle_db_table_view(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Просмотр конкретной таблицы БД"""
        query = update.callback_query
        await query.answer()
        
        # Проверяем admin ID
        user_tg = update.effective_user
        if not PermissionService.is_admin_by_id(str(user_tg.id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        # Парсим callback_data
        from core.callbacks import CallbackBuilder
        _, _, params = CallbackBuilder.parse(query.data)
        
        if len(params) < 2:
            await query.answer("❌ Ошибка параметров", show_alert=True)
            return
        
        table_name = params[0]
        page = int(params[1])
        
        # Получаем данные из БД
        try:
            data = await self._get_table_data(table_name, page)
            
            if not data:
                text = f"🗄️ **Таблица: {table_name}**\n\n❌ Нет данных"
                keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=AdminCallback.database())]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                return
            
            # Форматируем данные
            text = await self._format_table_data(table_name, data, page)
            
            # Кнопки навигации
            keyboard = []
            nav_buttons = []
            
            if page > 0:
                nav_buttons.append(
                    InlineKeyboardButton("⬅️ Назад", callback_data=AdminCallback.db_table(table_name, page - 1))
                )
            
            if len(data) >= 10:  # Если есть еще данные
                nav_buttons.append(
                    InlineKeyboardButton("➡️ Вперед", callback_data=AdminCallback.db_table(table_name, page + 1))
                )
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            keyboard.append([InlineKeyboardButton("🔙 К таблицам", callback_data=AdminCallback.database())])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        except Exception as e:
            await query.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    
    async def _get_table_data(self, table_name: str, page: int = 0, limit: int = 10):
        """Получить данные из таблицы"""
        offset = page * limit
        
        async with self.user_repo.pool.acquire() as conn:
            # Проверяем существование таблицы
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                )
                """,
                table_name
            )
            
            if not table_exists:
                return None
            
            # Получаем данные
            rows = await conn.fetch(
                f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT $1 OFFSET $2",
                limit, offset
            )
            
            return rows
    
    async def _format_table_data(self, table_name: str, data, page: int) -> str:
        """Форматировать данные таблицы для отображения"""
        
        if table_name == "users":
            return self._format_users_table(data, page)
        elif table_name == "game_history":
            return self._format_game_history_table(data, page)
        elif table_name == "tickets":
            return self._format_tickets_table(data, page)
        elif table_name == "achievements":
            return self._format_achievements_table(data, page)
        else:
            # Общий формат для неизвестных таблиц
            return self._format_generic_table(table_name, data, page)
    
    def _format_users_table(self, data, page: int) -> str:
        """Форматировать таблицу users"""
        text = f"🗄️ **Таблица: Users** (стр. {page + 1})\n\n"
        
        for row in data:
            text += f"**ID:** {row['id']}\n"
            text += f"👤 {row['first_name']} (@{row['username'] or 'нет'})\n"
            text += f"💎 XP: {row['xp']} | 🪙 Монеты: {row['coins']}\n"
            text += f"🏆 Ранг: {row['rank_id']} | 🎭 Роль: {row['role']}\n"
            
            if row.get('discord_id'):
                text += f"🎮 Discord: {row['discord_id']}\n"
            
            text += f"📅 Создан: {row['created_at'].strftime('%Y-%m-%d')}\n"
            text += "─" * 30 + "\n\n"
        
        return text
    
    def _format_game_history_table(self, data, page: int) -> str:
        """Форматировать таблицу game_history"""
        text = f"🗄️ **Таблица: Game History** (стр. {page + 1})\n\n"
        
        for row in data:
            text += f"**ID:** {row['id']}\n"
            text += f"👤 User ID: {row['user_id']}\n"
            text += f"🎮 Игра: {row['game_type']}\n"
            text += f"{'✅ Победа' if row['won'] else '❌ Проигрыш'}\n"
            text += f"💰 Ставка: {row['bet_amount']} | Выигрыш: {row['win_amount']}\n"
            text += f"📅 {row['played_at'].strftime('%Y-%m-%d %H:%M')}\n"
            text += "─" * 30 + "\n\n"
        
        return text
    
    def _format_tickets_table(self, data, page: int) -> str:
        """Форматировать таблицу tickets"""
        text = f"🗄️ **Таблица: Tickets** (стр. {page + 1})\n\n"
        
        for row in data:
            status_emoji = {"open": "🟢", "in_progress": "🟡", "closed": "🔴"}.get(row['status'], "⚪")
            
            text += f"**ID:** {row['id']} {status_emoji}\n"
            text += f"👤 User ID: {row['user_id']}\n"
            text += f"📁 Категория: {row['category']}\n"
            text += f"⚡ Приоритет: {row['priority']}\n"
            text += f"📝 {row['subject'][:50]}...\n"
            text += f"📅 {row['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            text += "─" * 30 + "\n\n"
        
        return text
    
    def _format_achievements_table(self, data, page: int) -> str:
        """Форматировать таблицу achievements"""
        text = f"🗄️ **Таблица: Achievements** (стр. {page + 1})\n\n"
        
        for row in data:
            text += f"**ID:** {row['id']}\n"
            text += f"🏆 {row['name']}\n"
            text += f"📝 {row['description'][:50]}...\n"
            text += f"⭐ Редкость: {row['rarity']}\n"
            text += f"🎁 Награда: {row['reward_xp']} XP, {row['reward_coins']} монет\n"
            text += "─" * 30 + "\n\n"
        
        return text
    
    def _format_generic_table(self, table_name: str, data, page: int) -> str:
        """Общий формат для любой таблицы"""
        text = f"🗄️ **Таблица: {table_name}** (стр. {page + 1})\n\n"
        
        for row in data:
            text += f"**Запись ID: {row.get('id', 'N/A')}**\n"
            
            # Показываем первые 5 полей
            fields = list(row.keys())[:5]
            for field in fields:
                value = row[field]
                if value is not None:
                    # Обрезаем длинные значения
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:50] + "..."
                    text += f"• {field}: {str_value}\n"
            
            text += "─" * 30 + "\n\n"
        
        return text
