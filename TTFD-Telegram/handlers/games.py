"""
Обработчики игр с FSM
Версия 1.0 - Угадай число, Квиз, Ежедневный спин
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.games import (
    start_guess_number, check_guess_number,
    get_random_quiz, check_quiz_answer,
    can_spin, spin_wheel, get_game_stats, update_game_stats
)
from database import db

# Состояния FSM
GAME_GUESS_BET, GAME_GUESS_NUMBER = range(2)
GAME_QUIZ_BET, GAME_QUIZ_ANSWER = range(10, 12)

# ============================================================================
# МЕНЮ ИГР
# ============================================================================

async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню игр"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    db_user = db.get_user(telegram_id)
    
    text = f"""
🎮 **Игры TTFD**

💰 Твой баланс: {db_user['coins']} монет
✨ XP: {db_user['xp']}

Выбери игру:
"""
    
    keyboard = [
        [InlineKeyboardButton("🎲 Угадай число", callback_data="game_guess_start")],
        [InlineKeyboardButton("🧠 Квиз", callback_data="game_quiz_start")],
        [InlineKeyboardButton("🎰 Ежедневный спин", callback_data="game_spin_start")],
        [InlineKeyboardButton("📊 Моя статистика", callback_data="game_stats")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def game_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Статистика игр пользователя"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    stats = get_game_stats(telegram_id)
    
    win_rate = 0
    if stats['games_played'] > 0:
        win_rate = (stats['games_won'] / stats['games_played']) * 100
    
    text = f"""
📊 **Твоя игровая статистика**

🎮 Игр сыграно: {stats['games_played']}
🏆 Побед: {stats['games_won']}
📈 Процент побед: {win_rate:.1f}%
💰 Всего выиграно монет: {stats['total_coins_won']}
"""
    
    keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ============================================================================
# УГАДАЙ ЧИСЛО
# ============================================================================

async def game_guess_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало игры "Угадай число" - выбор ставки"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    db_user = db.get_user(telegram_id)
    
    text = f"""
🎲 **Угадай число**

Я загадал число от 1 до 10.
Угадаешь - получишь ставку × 3!

💰 Твой баланс: {db_user['coins']} монет

Выбери ставку:
"""
    
    keyboard = [
        [InlineKeyboardButton("10 💰", callback_data="game_guess_bet_10")],
        [InlineKeyboardButton("25 💰", callback_data="game_guess_bet_25")],
        [InlineKeyboardButton("50 💰", callback_data="game_guess_bet_50")],
        [InlineKeyboardButton("100 💰", callback_data="game_guess_bet_100")],
        [InlineKeyboardButton("❌ Отмена", callback_data="game_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return GAME_GUESS_BET

async def game_guess_bet_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ставка выбрана - начинаем игру"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    
    # Получаем ставку из callback_data
    bet_amount = int(query.data.replace('game_guess_bet_', ''))
    
    # Начинаем игру
    result = start_guess_number(telegram_id, bet_amount)
    
    if not result['success']:
        await query.answer(result['error'], show_alert=True)
        await query.edit_message_text(
            f"❌ {result['error']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]])
        )
        return ConversationHandler.END
    
    # Сохраняем данные игры
    context.user_data['game_guess_number'] = result['number']
    context.user_data['game_guess_bet'] = bet_amount
    
    text = f"""
🎲 **Угадай число**

Ставка: {bet_amount} 💰
Загадано число от 1 до 10

Выбери число:
"""
    
    keyboard = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(str(i), callback_data=f"game_guess_num_{i}"))
        if len(row) == 5:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="game_guess_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return GAME_GUESS_NUMBER

async def game_guess_number_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Число выбрано - проверяем результат"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    
    guessed_number = int(query.data.replace('game_guess_num_', ''))
    secret_number = context.user_data.get('game_guess_number')
    bet_amount = context.user_data.get('game_guess_bet')
    
    # Проверяем результат
    result = check_guess_number(telegram_id, secret_number, guessed_number, bet_amount)
    
    # Обновляем статистику
    update_game_stats(telegram_id, won=result['won'], coins_won=result['reward_coins'])
    
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
    
    # Очищаем данные
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Играть ещё", callback_data="game_guess_start")],
        [InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return ConversationHandler.END

async def game_guess_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена игры - возврат ставки"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    bet_amount = context.user_data.get('game_guess_bet', 0)
    
    # Возвращаем ставку
    if bet_amount > 0:
        db.add_coins(telegram_id, bet_amount)
    
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❌ Игра отменена. Ставка возвращена.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# ============================================================================
# КВИЗ
# ============================================================================

async def game_quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало квиза - выбор ставки"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    db_user = db.get_user(telegram_id)
    
    text = f"""
🧠 **Квиз**

Ответь на вопрос правильно - получишь ставку × 2!
Неправильно - потеряешь ставку.

💰 Твой баланс: {db_user['coins']} монет

Выбери ставку:
"""
    
    keyboard = [
        [InlineKeyboardButton("10 💰", callback_data="game_quiz_bet_10")],
        [InlineKeyboardButton("25 💰", callback_data="game_quiz_bet_25")],
        [InlineKeyboardButton("50 💰", callback_data="game_quiz_bet_50")],
        [InlineKeyboardButton("100 💰", callback_data="game_quiz_bet_100")],
        [InlineKeyboardButton("❌ Отмена", callback_data="game_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return GAME_QUIZ_BET

async def game_quiz_bet_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ставка выбрана - показываем вопрос"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    
    bet_amount = int(query.data.replace('game_quiz_bet_', ''))
    
    # Проверка баланса
    db_user = db.get_user(telegram_id)
    if db_user['coins'] < bet_amount:
        await query.answer(f"Недостаточно монет! У тебя: {db_user['coins']}", show_alert=True)
        await query.edit_message_text(
            f"❌ Недостаточно монет!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]])
        )
        return ConversationHandler.END
    
    # Снимаем ставку
    db.remove_coins(telegram_id, bet_amount)
    
    # Получаем случайный вопрос
    quiz = get_random_quiz()
    
    # Сохраняем данные
    context.user_data['game_quiz_correct'] = quiz['correct']
    context.user_data['game_quiz_bet'] = bet_amount
    context.user_data['game_quiz_question'] = quiz['question']
    
    text = f"""
🧠 **Квиз**

Ставка: {bet_amount} 💰

❓ **Вопрос:**
{quiz['question']}
"""
    
    keyboard = []
    for i, option in enumerate(quiz['options']):
        keyboard.append([InlineKeyboardButton(option, callback_data=f"game_quiz_ans_{i}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="game_quiz_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return GAME_QUIZ_ANSWER

async def game_quiz_answer_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ответ выбран - проверяем результат"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    
    user_answer = int(query.data.replace('game_quiz_ans_', ''))
    correct_answer = context.user_data.get('game_quiz_correct')
    bet_amount = context.user_data.get('game_quiz_bet')
    
    # Проверяем ответ
    result = check_quiz_answer(telegram_id, correct_answer, user_answer, bet_amount)
    
    # Обновляем статистику
    update_game_stats(telegram_id, won=result['correct'], coins_won=result['reward_coins'])
    
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
    
    # Очищаем данные
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("🔄 Играть ещё", callback_data="game_quiz_start")],
        [InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return ConversationHandler.END

async def game_quiz_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена квиза - возврат ставки"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    bet_amount = context.user_data.get('game_quiz_bet', 0)
    
    # Возвращаем ставку
    if bet_amount > 0:
        db.add_coins(telegram_id, bet_amount)
    
    context.user_data.clear()
    
    keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❌ Игра отменена. Ставка возвращена.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# ============================================================================
# ЕЖЕДНЕВНЫЙ СПИН
# ============================================================================

async def game_spin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ежедневный спин"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    
    # Проверка кулдауна
    check = can_spin(telegram_id)
    
    if not check['can_spin']:
        text = f"""
⏰ **Ежедневный спин**

Ты уже крутил сегодня!
Следующий спин через: {check['time_left']}

Возвращайся завтра! 🌙
"""
        keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        return
    
    text = """
🎰 **Ежедневный спин**

Крути колесо фортуны и получи награду!
Доступно 1 раз в 24 часа.

Возможные награды:
💰 10-200 монет
💎 50 XP
🎉 ДЖЕКПОТ - 500 монет!
"""
    
    keyboard = [
        [InlineKeyboardButton("🎰 КРУТИТЬ!", callback_data="game_spin_do")],
        [InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def game_spin_do(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Крутим спин"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    telegram_id = str(user.id)
    
    # Крутим
    result = spin_wheel(telegram_id)
    
    if not result['success']:
        await query.answer(result['error'], show_alert=True)
        await query.edit_message_text(
            f"❌ {result['error']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]])
        )
        return
    
    reward = result['reward']
    
    text = f"""
🎰 **Результат спина!**

🎉 Ты получил: **{reward['name']}**

"""
    
    if reward['coins'] > 0:
        text += f"💰 +{reward['coins']} монет\n"
    
    if reward['xp'] > 0:
        text += f"✨ +{reward['xp']} XP\n"
    
    text += "\nВозвращайся завтра за новой наградой! 🌙"
    
    keyboard = [[InlineKeyboardButton("🔙 К играм", callback_data="game_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
