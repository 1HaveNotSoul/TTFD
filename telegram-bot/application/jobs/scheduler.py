"""
Job Scheduler - планировщик фоновых задач
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from domain.services.user_service import UserService
from domain.services.game_service import GameService

logger = logging.getLogger(__name__)


class JobScheduler:
    """Планировщик фоновых задач"""
    
    def __init__(
        self,
        user_service: UserService,
        game_service: GameService
    ):
        self.user_service = user_service
        self.game_service = game_service
        self.scheduler = AsyncIOScheduler()
    
    def setup_jobs(self):
        """Настроить все задачи"""
        
        # Ежедневный ресет (00:00)
        self.scheduler.add_job(
            self.daily_reset,
            CronTrigger(hour=0, minute=0),
            id='daily_reset',
            name='Ежедневный ресет',
            replace_existing=True
        )
        
        # Еженедельная статистика (понедельник 09:00)
        self.scheduler.add_job(
            self.weekly_stats,
            CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_stats',
            name='Еженедельная статистика',
            replace_existing=True
        )
        
        # Очистка старых данных (каждый день в 03:00)
        self.scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(hour=3, minute=0),
            id='cleanup_old_data',
            name='Очистка старых данных',
            replace_existing=True
        )
        
        logger.info("✅ Фоновые задачи настроены")
    
    def start(self):
        """Запустить планировщик"""
        self.scheduler.start()
        logger.info("🚀 Планировщик запущен")
    
    def shutdown(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
        logger.info("🛑 Планировщик остановлен")
    
    # ========================================================================
    # ЗАДАЧИ
    # ========================================================================
    
    async def daily_reset(self):
        """Ежедневный ресет (00:00)"""
        logger.info("🔄 Запуск ежедневного ресета...")
        
        try:
            # Здесь можно добавить логику ресета дейликов
            # Например, сброс счётчиков, обновление статистики и т.д.
            
            logger.info("✅ Ежедневный ресет завершён")
        
        except Exception as e:
            logger.error(f"❌ Ошибка ежедневного ресета: {e}")
    
    async def weekly_stats(self):
        """Еженедельная статистика (понедельник 09:00)"""
        logger.info("📊 Генерация еженедельной статистики...")
        
        try:
            # Получаем топ игроков за неделю
            leaderboard = await self.user_service.get_leaderboard(limit=10)
            
            # Статистика игр
            # game_stats = await self.game_service.get_leaderboard(limit=10)
            
            logger.info(f"✅ Статистика сгенерирована: {len(leaderboard)} пользователей")
        
        except Exception as e:
            logger.error(f"❌ Ошибка генерации статистики: {e}")
    
    async def cleanup_old_data(self):
        """Очистка старых данных (каждый день в 03:00)"""
        logger.info("🧹 Очистка старых данных...")
        
        try:
            # Здесь можно добавить логику очистки:
            # - Удаление старых логов
            # - Архивация старых тикетов
            # - Очистка кэша
            
            logger.info("✅ Очистка завершена")
        
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")
