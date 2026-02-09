"""
Game Router - маршрутизация всех игровых callback
Централизованная регистрация handlers для домена GAME
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

from core.callbacks import CallbackBuilder, CallbackDomain
from application.handlers.games.guess_handler import GuessGameHandler
from application.handlers.games.quiz_handler import QuizHandler
from application.handlers.games.spin_handler import SpinHandler
from application.handlers.games.games_menu_handler import GamesMenuHandler

logger = logging.getLogger(__name__)


class GameRouter:
    """
    Роутер для всех игровых callback
    
    Обрабатывает все callback с доменом GAME:
    - game:menu - главное меню игр
    - game:stats - статистика игр
    - game:guess:* - игра "Угадай число"
    - game:quiz:* - квиз
    - game:spin:* - ежедневный спин
    """
    
    def __init__(
        self,
        guess_handler: GuessGameHandler,
        quiz_handler: QuizHandler,
        spin_handler: SpinHandler,
        menu_handler: GamesMenuHandler
    ):
        self.guess_handler = guess_handler
        self.quiz_handler = quiz_handler
        self.spin_handler = spin_handler
        self.menu_handler = menu_handler
    
    async def route(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Маршрутизировать игровой callback к нужному handler
        
        Args:
            update: Telegram Update
            context: Telegram Context
        """
        query = update.callback_query
        
        if not query:
            return
        
        callback_data = query.data
        
        try:
            domain, action, params = CallbackBuilder.parse(callback_data)
            
            # Проверяем что это игровой callback
            if domain != CallbackDomain.GAME.value:
                logger.warning(f"⚠️  GameRouter получил не-игровой callback: {callback_data}")
                return
            
            # Маршрутизация по action
            
            # Главное меню игр
            if action == "menu":
                await self.menu_handler.handle_menu(update, context)
                return
            
            # Статистика игр
            if action == "stats":
                await self.menu_handler.handle_stats(update, context)
                return
            
            # Игра "Угадай число"
            if action == "guess":
                await self._route_guess(update, context, params)
                return
            
            # Квиз
            if action == "quiz":
                await self._route_quiz(update, context, params)
                return
            
            # Спин
            if action == "spin":
                await self._route_spin(update, context, params)
                return
            
            # Неизвестное действие
            logger.warning(f"⚠️  Неизвестное игровое действие: {action}")
            await query.answer("❌ Неизвестная игра", show_alert=True)
        
        except ValueError as e:
            logger.error(f"❌ Ошибка парсинга callback: {e}")
            await query.answer("❌ Ошибка обработки", show_alert=True)
        
        except Exception as e:
            logger.error(f"❌ Ошибка в GameRouter: {e}", exc_info=True)
            await query.answer("❌ Произошла ошибка", show_alert=True)
    
    async def _route_guess(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        params: list[str]
    ):
        """Маршрутизация для игры "Угадай число" """
        if not params:
            logger.warning("⚠️  Guess callback без параметров")
            return
        
        sub_action = params[0]
        
        # game:guess:start
        if sub_action == "start":
            await self.guess_handler.handle_start(update, context)
        
        # game:guess:bet:50
        elif sub_action == "bet":
            await self.guess_handler.handle_bet_selected(update, context)
        
        # game:guess:num:5
        elif sub_action == "num":
            await self.guess_handler.handle_number_selected(update, context)
        
        # game:guess:cancel
        elif sub_action == "cancel":
            await self.guess_handler.handle_cancel(update, context)
        
        else:
            logger.warning(f"⚠️  Неизвестное действие guess: {sub_action}")
    
    async def _route_quiz(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        params: list[str]
    ):
        """Маршрутизация для квиза"""
        if not params:
            logger.warning("⚠️  Quiz callback без параметров")
            return
        
        sub_action = params[0]
        
        # game:quiz:start
        if sub_action == "start":
            await self.quiz_handler.handle_start(update, context)
        
        # game:quiz:bet:50
        elif sub_action == "bet":
            await self.quiz_handler.handle_bet_selected(update, context)
        
        # game:quiz:ans:2
        elif sub_action == "ans":
            await self.quiz_handler.handle_answer_selected(update, context)
        
        # game:quiz:cancel
        elif sub_action == "cancel":
            await self.quiz_handler.handle_cancel(update, context)
        
        else:
            logger.warning(f"⚠️  Неизвестное действие quiz: {sub_action}")
    
    async def _route_spin(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        params: list[str]
    ):
        """Маршрутизация для спина"""
        if not params:
            logger.warning("⚠️  Spin callback без параметров")
            return
        
        sub_action = params[0]
        
        # game:spin:start
        if sub_action == "start":
            await self.spin_handler.handle_start(update, context)
        
        # game:spin:do
        elif sub_action == "do":
            await self.spin_handler.handle_spin(update, context)
        
        else:
            logger.warning(f"⚠️  Неизвестное действие spin: {sub_action}")
