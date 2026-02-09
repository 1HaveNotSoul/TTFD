"""
TTFD Telegram Bot v3.0 - Clean Architecture
Рефакторинг Шаг 1: Централизованные callback и state management
Шаг 2: Игровая мета (Сезоны)
"""
import asyncio
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler

logger = logging.getLogger(__name__)

# Core
from core.config import Config
from core.callbacks import CallbackDomain
from core.state_manager import state_manager

# Infrastructure
from infrastructure.database.connection import db_connection
from infrastructure.database.repositories.user_repository import UserRepository
from infrastructure.database.repositories.game_repository import GameRepository
from infrastructure.database.repositories.ticket_repository import TicketRepository
from infrastructure.database.repositories.season_repository import SeasonRepository
from infrastructure.database.repositories.achievement_repository import AchievementRepository
from infrastructure.database.repositories.discord_repository import DiscordRepository
from infrastructure.cache.redis_cache import RedisCache, MemoryCache
from infrastructure.external.discord_client import DiscordClient

# Domain
from domain.services.user_service import UserService
from domain.services.permission_service import PermissionService
from domain.services.game_service import GameService
from domain.services.ticket_service import TicketService
from domain.services.season_service import SeasonService
from domain.services.achievement_service import AchievementService
from domain.services.discord_service import DiscordService

# Application
from application.router import callback_router
from application.handlers.user.profile_handler import ProfileHandler
from application.handlers.user.leaderboard_handler import LeaderboardHandler
from application.handlers.economy.daily_handler import DailyHandler
from application.handlers.admin.admin_handler import AdminHandler
from application.handlers.games.guess_handler import GuessGameHandler
from application.handlers.games.quiz_handler import QuizHandler
from application.handlers.games.spin_handler import SpinHandler
from application.handlers.games.games_menu_handler import GamesMenuHandler
from application.handlers.games.game_router import GameRouter
from application.handlers.tickets.ticket_handler import TicketHandler
from application.handlers.tickets.admin_ticket_handler import AdminTicketHandler
from application.handlers.tickets.ticket_router import TicketRouter
from application.handlers.admin.admin_router import AdminRouter
from application.handlers.season.season_handler import SeasonHandler
from application.handlers.achievement.achievement_handler import AchievementHandler
from application.handlers.discord.discord_handler import DiscordHandler


async def start_command(update: Update, context):
    """Команда /start"""
    await update.message.reply_text(
        "👋 Привет! Я TTFD Bot v3.0\n\n"
        "Доступные команды:\n"
        "/profile - Твой профиль\n"
        "/daily - Ежедневная награда\n"
        "/games - Игры\n"
        "/season - Текущий сезон 🏆\n"
        "/achievements - Достижения 🏅\n"
        "/discord - Discord интеграция 🔗\n"
        "/tickets - Тикеты поддержки\n"
        "/leaderboard - Таблица лидеров\n"
        "/help - Помощь"
    )


async def help_command(update: Update, context):
    """Команда /help"""
    await update.message.reply_text(
        "📖 Помощь TTFD Bot v3.0\n\n"
        "👤 Профиль:\n"
        "/profile - Посмотреть свой профиль\n"
        "/leaderboard - Таблица лидеров\n\n"
        "💰 Экономика:\n"
        "/daily - Ежедневная награда (100 XP + 50 монет)\n\n"
        "🎮 Игры:\n"
        "/games - Меню игр (Угадай число, Квиз, Спин)\n\n"
        "🏆 Сезоны:\n"
        "/season - Текущий сезон и твой прогресс\n\n"
        "🏅 Достижения:\n"
        "/achievements - Твои достижения и награды\n\n"
        "🔗 Discord:\n"
        "/discord - Привязка Discord и автоматические роли\n\n"
        "🎫 Поддержка:\n"
        "/tickets - Тикеты поддержки\n\n"
        "🔧 Админ (только для админов):\n"
        "/admin - Админ-панель\n"
        "/admin_stats - Статистика платформы\n"
        "/setrole <id> <role> - Изменить роль\n"
        "/broadcast <текст> - Рассылка\n\n"
        "ℹ️ Прочее:\n"
        "/start - Начать работу с ботом\n"
        "/help - Эта справка"
    )


async def main():
    """Запуск бота"""
    print("=" * 60)
    print("🚀 Запуск TTFD Telegram Bot v3.0 (Clean Architecture)")
    print("=" * 60)
    
    # Валидация конфигурации
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Подключаемся к PostgreSQL
    print("\n📡 Подключение к PostgreSQL...")
    try:
        await db_connection.connect()
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        print("💡 Убедись что PostgreSQL запущен и DATABASE_URL правильный")
        sys.exit(1)
    
    # Подключаемся к Redis (или используем MemoryCache)
    print("\n📡 Подключение к Redis...")
    try:
        cache = RedisCache(Config.REDIS_URL)
        await cache.connect()
    except Exception as e:
        print(f"⚠️  Redis недоступен, используем MemoryCache: {e}")
        cache = MemoryCache()
        await cache.connect()
    
    # Создаём repositories
    print("\n🔧 Инициализация repositories...")
    user_repo = UserRepository(db_connection.get_pool())
    game_repo = GameRepository(db_connection.get_pool())
    ticket_repo = TicketRepository(db_connection.get_pool())
    season_repo = SeasonRepository(db_connection.get_pool())
    achievement_repo = AchievementRepository(db_connection.get_pool())
    discord_repo = DiscordRepository(db_connection.get_pool())
    
    # Создаём Discord клиент (опционально)
    discord_client = None
    if Config.DISCORD_BOT_TOKEN and Config.DISCORD_GUILD_ID:
        print("🔧 Инициализация Discord клиента...")
        discord_client = DiscordClient(
            bot_token=Config.DISCORD_BOT_TOKEN,
            guild_id=Config.DISCORD_GUILD_ID
        )
    else:
        print("⚠️  Discord интеграция отключена (нет токена/guild_id)")
    
    # Создаём services (с кэшем)
    print("🔧 Инициализация services...")
    user_service = UserService(user_repo, cache)
    discord_service = DiscordService(discord_repo, discord_client)
    achievement_service = AchievementService(achievement_repo, user_service, discord_service)
    season_service = SeasonService(season_repo, user_service, achievement_service, discord_service)
    game_service = GameService(game_repo, user_service, season_service, achievement_service)
    ticket_service = TicketService(ticket_repo, user_service)
    
    # Создаём handlers
    print("🔧 Инициализация handlers...")
    profile_handler = ProfileHandler(user_service)
    daily_handler = DailyHandler(user_service)
    leaderboard_handler = LeaderboardHandler(user_service)
    admin_handler = AdminHandler(user_service)
    
    # Игровые handlers
    guess_handler = GuessGameHandler(game_service, user_service)
    quiz_handler = QuizHandler(game_service, user_service)
    spin_handler = SpinHandler(game_service, user_service)
    games_menu_handler = GamesMenuHandler(game_service, user_service)
    
    # Игровой роутер
    game_router = GameRouter(
        guess_handler,
        quiz_handler,
        spin_handler,
        games_menu_handler
    )
    
    # Тикетные handlers
    ticket_handler = TicketHandler(ticket_service, user_service)
    admin_ticket_handler = AdminTicketHandler(ticket_service, user_service)
    
    # Тикетный роутер
    ticket_router = TicketRouter(ticket_handler, admin_ticket_handler)
    
    # Админский роутер
    admin_router = AdminRouter(admin_handler, admin_ticket_handler)
    
    # Сезонный handler
    season_handler = SeasonHandler(season_service, user_service)
    
    # Достижения handler
    achievement_handler = AchievementHandler(achievement_service, user_service)
    
    # Discord handler
    discord_handler = DiscordHandler(discord_service, user_service)
    
    # Создаём приложение
    print("\n🤖 Создание Telegram приложения...")
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем handlers
    print("📝 Регистрация handlers...")
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_handler.handle_profile_command))
    app.add_handler(CommandHandler("daily", daily_handler.handle_daily_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler.handle_leaderboard_command))
    
    # Админ-команды
    app.add_handler(CommandHandler("admin", admin_handler.handle_admin_command))
    app.add_handler(CommandHandler("admin_stats", admin_handler.handle_stats_command))
    app.add_handler(CommandHandler("setrole", admin_handler.handle_set_role_command))
    app.add_handler(CommandHandler("broadcast", admin_handler.handle_broadcast_command))
    
    # Игровые команды
    app.add_handler(CommandHandler("games", games_menu_handler.handle_menu))
    
    # Тикетные команды
    app.add_handler(CommandHandler("tickets", ticket_handler.handle_menu))
    
    # Сезонные команды
    app.add_handler(CommandHandler("season", season_handler.handle_season_info))
    
    # Достижения команды
    app.add_handler(CommandHandler("achievements", achievement_handler.handle_achievements_command))
    
    # Discord команды
    app.add_handler(CommandHandler("discord", discord_handler.handle_discord_command))
    
    # Регистрируем callback роутер
    print("📝 Регистрация callback router...")
    callback_router.register_domain(CallbackDomain.GAME, game_router.route)
    callback_router.register_domain(CallbackDomain.TICKET, ticket_router.route)
    callback_router.register_domain(CallbackDomain.ADMIN, admin_router.route)
    
    # Регистрируем сезонные callback
    callback_router.register_exact("season_info", season_handler.handle_season_info)
    callback_router.register_exact("season_leaderboard", season_handler.handle_leaderboard)
    callback_router.register_exact("season_rewards", season_handler.handle_rewards)
    
    # Регистрируем достижения callback
    callback_router.register_exact("ach_menu", achievement_handler.handle_achievements_command)
    callback_router.register_exact("ach_list_all", achievement_handler.handle_list_all)
    callback_router.register_exact("ach_list_completed", achievement_handler.handle_list_completed)
    callback_router.register_exact("ach_cat_games", achievement_handler.handle_category)
    callback_router.register_exact("ach_cat_activity", achievement_handler.handle_category)
    callback_router.register_exact("ach_cat_streak", achievement_handler.handle_category)
    callback_router.register_exact("ach_cat_season", achievement_handler.handle_category)
    callback_router.register_exact("ach_cat_tickets", achievement_handler.handle_category)
    callback_router.register_exact("ach_claim_all", achievement_handler.handle_claim_all)
    
    # Регистрируем Discord callback
    callback_router.register_exact("discord_menu", discord_handler.handle_discord_command)
    callback_router.register_exact("discord_link_start", discord_handler.handle_link_start)
    callback_router.register_exact("discord_unlink", discord_handler.handle_unlink)
    callback_router.register_exact("discord_roles", discord_handler.handle_roles)
    callback_router.register_exact("discord_status", discord_handler.handle_status)
    callback_router.register_exact("discord_help", discord_handler.handle_help)
    
    app.add_handler(callback_router.get_handler())
    
    # Регистрируем message handler для текста тикетов
    app.add_handler(ticket_router.get_message_handler())
    
    # Запускаем фоновую задачу очистки состояний
    print("🧹 Запуск фоновых задач...")
    
    async def cleanup_states():
        """Периодическая очистка истекших состояний"""
        while True:
            await asyncio.sleep(300)  # Каждые 5 минут
            state_manager.cleanup_expired()
    
    async def check_season():
        """Проверка окончания сезона и обновление рангов"""
        while True:
            await asyncio.sleep(3600)  # Каждый час
            try:
                await season_service.check_season_end()
                await season_service.update_all_ranks()
            except Exception as e:
                logger.error(f"Ошибка в check_season: {e}")
    
    async def process_discord_roles():
        """Обработка невыданных Discord ролей"""
        while True:
            await asyncio.sleep(300)  # Каждые 5 минут
            try:
                await discord_service.process_pending_role_grants()
                await discord_service.expire_old_codes()
            except Exception as e:
                logger.error(f"Ошибка в process_discord_roles: {e}")
    
    asyncio.create_task(cleanup_states())
    asyncio.create_task(check_season())
    asyncio.create_task(process_discord_roles())
    
    print("\n" + "=" * 60)
    print("✅ TTFD Bot v3.0 запущен и готов к работе!")
    print("   • Clean Architecture")
    print("   • PostgreSQL")
    print("   • Redis Cache" if cache.enabled else "   • Memory Cache (fallback)")
    print("   • Domain-Driven Design")
    print("   • Role-Based Access Control (RBAC)")
    print("   • Centralized Callback Router")
    print("   • State Manager with TTL")
    print("   • Season System (30 days)")
    print("   • Achievement System")
    print("   • Discord Integration" if discord_client else "   • Discord Integration (disabled)")
    print("=" * 60)
    print("\n💡 Отправь /start, /games, /season, /achievements или /discord боту в Telegram\n")
    
    # Запускаем бота
    try:
        await app.run_polling(drop_pending_updates=True)
    finally:
        # Закрываем подключения
        await db_connection.disconnect()
        await cache.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
