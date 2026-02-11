"""
Guess Game Handler - игра "Угадай число"
Рефакторинг: использует централизованные callback и state_manager
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.game_service import GameService
from domain.services.user_service import UserService
from core.exceptions import InsufficientFundsError
from core.callbacks import GameCallback, CallbackBuilder
from core.state_manager import state_manager, StateKey, StateTimeout


class GuessGameHandler:
    """Handler для игры "Угадай число" """
    
    def __init__(self, game_service: GameService, user_service: UserService):
        self.game_service = game_service
        self.user_service = user_service
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало игры - выбор ставки"""
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
🎲 **Угадай число**

Я загадал число от 1 до 10.
Угадаешь - получишь ставку × 3!

💰 Твой баланс: {user.coins} монет

Выбери ставку:
"""
        
        keyboard = [
            [InlineKeyboardButton("10 💰", callback_data=GameCallback.guess_bet(10))],
            [InlineKeyboardButton("25 💰", callback_data=GameCallback.guess_bet(25))],
            [InlineKeyboardButton("50 💰", callback_data=GameCallback.guess_bet(50))],
            [InlineKeyboardButton("100 💰", callback_data=GameCallback.guess_bet(100))],
            [InlineKeyboardButton("❌ Отмена", callback_data=GameCallback.menu())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_bet_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ставка выбрана - начинаем игру"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        # Парсим callback для получения ставки
        _, _, params = CallbackBuilder.parse(query.data)
        bet_amount = int(params[0])
        
        try:
            # Начинаем игру
            session, secret_number = await self.game_service.start_guess_game(user, bet_amount)
            
            # Сохраняем состояние через state_manager (вместо context.user_data)
            state_manager.set_state(
                user_id=user.id,
                state_key=StateKey.GAME_GUESS_ACTIVE,
                data={
                    'session_id': session.id,
                    'secret_number': secret_number,
                    'bet': bet_amount
                },
                timeout=StateTimeout.SHORT  # 5 минут на игру
            )
            
            text = f"""
🎲 **Угадай число**

Ставка: {bet_amount} 💰
Загадано число от 1 до 10

Выбери число:
"""
            
            keyboard = []
            row = []
            for i in range(1, 11):
                row.append(InlineKeyboardButton(str(i), callback_data=GameCallback.guess_number(i)))
                if len(row) == 5:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=GameCallback.guess_cancel())])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        except InsufficientFundsError as e:
            await query.answer(str(e), show_alert=True)
            await self.handle_start(update, context)
    
    async def handle_number_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Число выбрано - проверяем результат"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        
        # Получаем состояние через state_manager
        state = state_manager.get_state(int(user_tg.id), StateKey.GAME_GUESS_ACTIVE)
        
        if not state:
            await query.answer("⏰ Время игры истекло", show_alert=True)
            await self.handle_start(update, context)
            return
        
        # Парсим callback для получения числа
        _, _, params = CallbackBuilder.parse(query.data)
        guessed_number = int(params[0])
        
        session_id = state['session_id']
        secret_number = state['secret_number']
        bet_amount = state['bet']
        
        # Получаем сессию
        session = await self.game_service.game_repo.get_session(session_id)
        
        # Проверяем результат
        result = await self.game_service.check_guess(session, secret_number, guessed_number)
        
        if result['won']:
            text = f"""
🎉 **ПОБЕДА!**

Ты угадал число {secret_number}!

💰 Выигрыш: +{result['reward_coins']} монет
✨ XP: +{result['reward_xp']}
"""
        else:
            text = f"""
😔 **Не угадал...**

Загаданное число было: {secret_number}
Ты выбрал: {guessed_number}

💰 Потеряно: -{bet_amount} монет
✨ Утешительный XP: +{result['reward_xp']}
"""
        
        # Очищаем состояние
        state_manager.clear_state(int(user_tg.id), StateKey.GAME_GUESS_ACTIVE)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Играть ещё", callback_data=GameCallback.guess_start())],
            [InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена игры - возврат ставки"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        
        # Получаем состояние
        state = state_manager.get_state(int(user_tg.id), StateKey.GAME_GUESS_ACTIVE)
        
        if state:
            session_id = state['session_id']
            session = await self.game_service.game_repo.get_session(session_id)
            await self.game_service.cancel_guess_game(session)
        
        # Очищаем состояние
        state_manager.clear_state(int(user_tg.id), StateKey.GAME_GUESS_ACTIVE)
        
        keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Игра отменена. Ставка возвращена.",
            reply_markup=reply_markup
        )
