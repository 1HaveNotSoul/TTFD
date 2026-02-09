"""
TTFD Telegram Bot - Главный файл
Версия 2.1 - Полноценная тикет-система + Игры
"""

import os
import sys
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler
)

# Импорты модулей
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_IDS
from database import db
from handlers.commands import (
    start_command, help_command, profile_command, 
    daily_command, leaderboard_command, link_command,
    ticket_command, mytickets_command
)
from handlers.buttons import button_handler
from handlers.messages import message_handler
from handlers.admin import admin_command, broadcast_command

# Импорты для системы кодов привязки (Discord → Telegram)
from handlers.discord_code import code_command, checklink_command, unlink_command

# Импорты для тикет-системы
from handlers.tickets import (
    TICKET_CATEGORY, TICKET_MESSAGE, TICKET_PRIORITY, TICKET_CONFIRM,
    TICKET_RESPONSE_MESSAGE,
    ticket_create_start, ticket_category_selected, ticket_message_received,
    ticket_priority_selected, ticket_confirm, ticket_cancel,
    ticket_reply_start, ticket_reply_message
)

# Импорты для игр
from handlers.games import (
    GAME_GUESS_BET, GAME_GUESS_NUMBER,
    GAME_QUIZ_BET, GAME_QUIZ_ANSWER,
    game_guess_start, game_guess_bet_selected, game_guess_number_selected, game_guess_cancel,
    game_quiz_start, game_quiz_bet_selected, game_quiz_answer_selected, game_quiz_cancel
)

def main():
    """Запуск бота"""
    print("=" * 50)
    print("🚀 Запуск TTFD Telegram Bot v2.1...")
    print("=" * 50)
    
    # Проверка токена
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_telegram_bot_token_here':
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        print("💡 Получи токен у @BotFather и добавь в .env файл")
        sys.exit(1)
    
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ========================================================================
    # CONVERSATION HANDLER: Создание тикета
    # ========================================================================
    ticket_create_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ticket_create_start, pattern="^ticket_create_start$")
        ],
        states={
            TICKET_CATEGORY: [
                CallbackQueryHandler(ticket_category_selected, pattern="^ticket_cat_"),
                CallbackQueryHandler(ticket_cancel, pattern="^ticket_cancel$")
            ],
            TICKET_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ticket_message_received),
                CallbackQueryHandler(ticket_cancel, pattern="^ticket_cancel$")
            ],
            TICKET_PRIORITY: [
                CallbackQueryHandler(ticket_priority_selected, pattern="^ticket_pri_"),
                CallbackQueryHandler(ticket_cancel, pattern="^ticket_cancel$")
            ],
            TICKET_CONFIRM: [
                CallbackQueryHandler(ticket_confirm, pattern="^ticket_confirm_yes$"),
                CallbackQueryHandler(ticket_cancel, pattern="^ticket_cancel$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(ticket_cancel, pattern="^ticket_cancel$")
        ],
        conversation_timeout=300  # 5 минут
    )
    
    # ========================================================================
    # CONVERSATION HANDLER: Ответ на тикет
    # ========================================================================
    ticket_reply_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ticket_reply_start, pattern="^ticket_reply_")
        ],
        states={
            TICKET_RESPONSE_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ticket_reply_message)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(button_handler, pattern="^ticket_view_")
        ],
        conversation_timeout=300
    )
    
    # ========================================================================
    # CONVERSATION HANDLER: Игра "Угадай число"
    # ========================================================================
    game_guess_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(game_guess_start, pattern="^game_guess_start$")
        ],
        states={
            GAME_GUESS_BET: [
                CallbackQueryHandler(game_guess_bet_selected, pattern="^game_guess_bet_"),
                CallbackQueryHandler(button_handler, pattern="^game_menu$")
            ],
            GAME_GUESS_NUMBER: [
                CallbackQueryHandler(game_guess_number_selected, pattern="^game_guess_num_"),
                CallbackQueryHandler(game_guess_cancel, pattern="^game_guess_cancel$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(button_handler, pattern="^game_menu$")
        ],
        conversation_timeout=180
    )
    
    # ========================================================================
    # CONVERSATION HANDLER: Игра "Квиз"
    # ========================================================================
    game_quiz_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(game_quiz_start, pattern="^game_quiz_start$")
        ],
        states={
            GAME_QUIZ_BET: [
                CallbackQueryHandler(game_quiz_bet_selected, pattern="^game_quiz_bet_"),
                CallbackQueryHandler(button_handler, pattern="^game_menu$")
            ],
            GAME_QUIZ_ANSWER: [
                CallbackQueryHandler(game_quiz_answer_selected, pattern="^game_quiz_ans_"),
                CallbackQueryHandler(game_quiz_cancel, pattern="^game_quiz_cancel$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(button_handler, pattern="^game_menu$")
        ],
        conversation_timeout=180
    )
    
    # ========================================================================
    # Регистрируем ConversationHandlers (ВАЖНО: до обычных CallbackQueryHandler!)
    # ========================================================================
    app.add_handler(ticket_create_conv)
    app.add_handler(ticket_reply_conv)
    app.add_handler(game_guess_conv)
    app.add_handler(game_quiz_conv)
    
    # ========================================================================
    # Регистрируем команды
    # ========================================================================
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("link", link_command))
    app.add_handler(CommandHandler("ticket", ticket_command))
    app.add_handler(CommandHandler("mytickets", mytickets_command))
    
    # Команды привязки через код (Discord → Telegram)
    app.add_handler(CommandHandler("code", code_command))
    app.add_handler(CommandHandler("checklink", checklink_command))
    app.add_handler(CommandHandler("unlink", unlink_command))
    
    # Админ команды
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # ========================================================================
    # Обработчики кнопок и сообщений
    # ========================================================================
    # Общий обработчик кнопок
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    print("✅ Все обработчики зарегистрированы")
    print("   • Тикет-система с FSM")
    print("   • Игры: Угадай число, Квиз, Ежедневный спин")
    print("   • Админ-панель тикетов")
    print("=" * 50)
    print("✅ Telegram бот запущен и готов к работе!")
    print("   Отправь /start боту в Telegram")
    print("=" * 50)
    
    # Запускаем бота
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
