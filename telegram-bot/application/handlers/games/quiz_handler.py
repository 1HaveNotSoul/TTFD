"""
Quiz Handler - игра "Квиз"
Рефакторинг: использует централизованные callback и state_manager
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from domain.services.game_service import GameService
from domain.services.user_service import UserService
from core.exceptions import InsufficientFundsError
from core.callbacks import GameCallback, CallbackBuilder
from core.state_manager import state_manager, StateKey, StateTimeout


class QuizHandler:
    """Handler для квиза"""
    
    def __init__(self, game_service: GameService, user_service: UserService):
        self.game_service = game_service
        self.user_service = user_service
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало квиза - выбор ставки"""
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
🧠 **Квиз**

Ответь на вопрос правильно - получишь ставку × 2!
Неправильно - потеряешь ставку.

💰 Твой баланс: {user.coins} монет

Выбери ставку:
"""
        
        keyboard = [
            [InlineKeyboardButton("10 💰", callback_data=GameCallback.quiz_bet(10))],
            [InlineKeyboardButton("25 💰", callback_data=GameCallback.quiz_bet(25))],
            [InlineKeyboardButton("50 💰", callback_data=GameCallback.quiz_bet(50))],
            [InlineKeyboardButton("100 💰", callback_data=GameCallback.quiz_bet(100))],
            [InlineKeyboardButton("❌ Отмена", callback_data=GameCallback.menu())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_bet_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ставка выбрана - показываем вопрос"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        user = await self.user_service.get_user(str(user_tg.id))
        
        # Парсим callback для получения ставки
        _, _, params = CallbackBuilder.parse(query.data)
        bet_amount = int(params[0])
        
        try:
            # Начинаем квиз
            session, quiz = await self.game_service.start_quiz_game(user, bet_amount)
            
            # Сохраняем состояние через state_manager
            state_manager.set_state(
                user_id=user.id,
                state_key=StateKey.GAME_QUIZ_ACTIVE,
                data={
                    'session_id': session.id,
                    'correct': quiz['correct'],
                    'bet': bet_amount
                },
                timeout=StateTimeout.SHORT  # 5 минут на ответ
            )
            
            text = f"""
🧠 **Квиз**

Ставка: {bet_amount} 💰

❓ **Вопрос:**
{quiz['question']}
"""
            
            keyboard = []
            for i, option in enumerate(quiz['options']):
                keyboard.append([InlineKeyboardButton(option, callback_data=GameCallback.quiz_answer(i))])
            
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=GameCallback.quiz_cancel())])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        except InsufficientFundsError as e:
            await query.answer(str(e), show_alert=True)
            await self.handle_start(update, context)
    
    async def handle_answer_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ответ выбран - проверяем результат"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        
        # Получаем состояние через state_manager
        state = state_manager.get_state(int(user_tg.id), StateKey.GAME_QUIZ_ACTIVE)
        
        if not state:
            await query.answer("⏰ Время игры истекло", show_alert=True)
            await self.handle_start(update, context)
            return
        
        # Парсим callback для получения ответа
        _, _, params = CallbackBuilder.parse(query.data)
        user_answer = int(params[0])
        
        session_id = state['session_id']
        correct_answer = state['correct']
        bet_amount = state['bet']
        
        # Получаем сессию
        session = await self.game_service.game_repo.get_session(session_id)
        
        # Проверяем ответ
        result = await self.game_service.check_quiz_answer(session, correct_answer, user_answer)
        
        if result['correct']:
            text = f"""
🎉 **ПРАВИЛЬНО!**

💰 Выигрыш: +{result['reward_coins']} монет
✨ XP: +{result['reward_xp']}
"""
        else:
            text = f"""
❌ **Неправильно...**

💰 Потеряно: {bet_amount} монет
✨ Утешительный XP: +{result['reward_xp']}
"""
        
        # Очищаем состояние
        state_manager.clear_state(int(user_tg.id), StateKey.GAME_QUIZ_ACTIVE)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Играть ещё", callback_data=GameCallback.quiz_start())],
            [InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена квиза"""
        query = update.callback_query
        await query.answer()
        
        user_tg = update.effective_user
        
        # Получаем состояние
        state = state_manager.get_state(int(user_tg.id), StateKey.GAME_QUIZ_ACTIVE)
        
        if state:
            session_id = state['session_id']
            session = await self.game_service.game_repo.get_session(session_id)
            await self.game_service.cancel_quiz_game(session)
        
        # Очищаем состояние
        state_manager.clear_state(int(user_tg.id), StateKey.GAME_QUIZ_ACTIVE)
        
        keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data=GameCallback.menu())]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "❌ Игра отменена. Ставка возвращена.",
            reply_markup=reply_markup
        )
