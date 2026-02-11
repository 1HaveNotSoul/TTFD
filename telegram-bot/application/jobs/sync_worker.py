"""
Sync Worker - фоновый процесс обработки событий синхронизации
"""
import asyncio
import logging
from typing import Optional

from domain.services.sync_service import SyncService

logger = logging.getLogger(__name__)


class SyncWorker:
    """Воркер для обработки очереди событий синхронизации"""
    
    def __init__(
        self,
        sync_service: SyncService,
        interval_seconds: int = 5,
        batch_size: int = 100
    ):
        """
        Args:
            sync_service: Сервис синхронизации
            interval_seconds: Интервал проверки очереди (секунды)
            batch_size: Размер батча для обработки
        """
        self.sync_service = sync_service
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Запустить воркер"""
        if self.is_running:
            logger.warning("⚠️  SyncWorker уже запущен")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run())
        
        logger.info(
            f"🚀 SyncWorker запущен: interval={self.interval_seconds}s, "
            f"batch_size={self.batch_size}"
        )
    
    async def stop(self):
        """Остановить воркер"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 SyncWorker остановлен")
    
    async def _run(self):
        """Основной цикл обработки"""
        logger.info("🔄 SyncWorker: начало обработки событий")
        
        while self.is_running:
            try:
                await self._process_batch()
            except Exception as e:
                logger.error(f"❌ Ошибка в SyncWorker: {e}")
            
            # Ждём перед следующей итерацией
            await asyncio.sleep(self.interval_seconds)
    
    async def _process_batch(self):
        """Обработать батч событий"""
        # Получаем pending события
        events = await self.sync_service.sync_repo.get_pending_events(
            limit=self.batch_size
        )
        
        if not events:
            return
        
        logger.info(f"📋 SyncWorker: обработка {len(events)} событий")
        
        processed = 0
        failed = 0
        
        for event in events:
            try:
                success = await self.sync_service.process_event(event)
                
                if success:
                    processed += 1
                else:
                    failed += 1
            
            except Exception as e:
                logger.error(
                    f"❌ Ошибка обработки события {event.id}: {e}"
                )
                failed += 1
        
        if processed > 0 or failed > 0:
            logger.info(
                f"✅ SyncWorker: обработано {processed}, "
                f"провалено {failed}"
            )
    
    async def process_now(self):
        """Принудительно обработать события сейчас"""
        logger.info("⚡ SyncWorker: принудительная обработка")
        await self._process_batch()


class ReconcileWorker:
    """Воркер для периодического reconcile"""
    
    def __init__(
        self,
        sync_service: SyncService,
        interval_minutes: int = 15,
        batch_size: int = 100
    ):
        """
        Args:
            sync_service: Сервис синхронизации
            interval_minutes: Интервал reconcile (минуты)
            batch_size: Размер батча пользователей
        """
        self.sync_service = sync_service
        self.interval_minutes = interval_minutes
        self.batch_size = batch_size
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Запустить воркер"""
        if self.is_running:
            logger.warning("⚠️  ReconcileWorker уже запущен")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run())
        
        logger.info(
            f"🚀 ReconcileWorker запущен: interval={self.interval_minutes}m, "
            f"batch_size={self.batch_size}"
        )
    
    async def stop(self):
        """Остановить воркер"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 ReconcileWorker остановлен")
    
    async def _run(self):
        """Основной цикл reconcile"""
        logger.info("🔄 ReconcileWorker: начало работы")
        
        while self.is_running:
            try:
                await self._reconcile_batch()
            except Exception as e:
                logger.error(f"❌ Ошибка в ReconcileWorker: {e}")
            
            # Ждём перед следующей итерацией
            await asyncio.sleep(self.interval_minutes * 60)
    
    async def _reconcile_batch(self):
        """Выполнить reconcile для батча пользователей"""
        logger.info("🔍 ReconcileWorker: проверка расхождений")
        
        results = await self.sync_service.reconcile_all_users(
            limit=self.batch_size
        )
        
        if results.get('status') == 'no_users':
            logger.info("✅ ReconcileWorker: нет пользователей для проверки")
            return
        
        logger.info(
            f"✅ ReconcileWorker: {results.get('completed', 0)} пользователей, "
            f"{results.get('issues_found', 0)} расхождений исправлено"
        )
    
    async def reconcile_now(self):
        """Принудительно запустить reconcile сейчас"""
        logger.info("⚡ ReconcileWorker: принудительный reconcile")
        await self._reconcile_batch()


class CleanupWorker:
    """Воркер для очистки старых событий"""
    
    def __init__(
        self,
        sync_service: SyncService,
        interval_hours: int = 24,
        retention_days: int = 30
    ):
        """
        Args:
            sync_service: Сервис синхронизации
            interval_hours: Интервал очистки (часы)
            retention_days: Хранить события N дней
        """
        self.sync_service = sync_service
        self.interval_hours = interval_hours
        self.retention_days = retention_days
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Запустить воркер"""
        if self.is_running:
            logger.warning("⚠️  CleanupWorker уже запущен")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run())
        
        logger.info(
            f"🚀 CleanupWorker запущен: interval={self.interval_hours}h, "
            f"retention={self.retention_days}d"
        )
    
    async def stop(self):
        """Остановить воркер"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 CleanupWorker остановлен")
    
    async def _run(self):
        """Основной цикл очистки"""
        logger.info("🔄 CleanupWorker: начало работы")
        
        while self.is_running:
            try:
                await self._cleanup()
            except Exception as e:
                logger.error(f"❌ Ошибка в CleanupWorker: {e}")
            
            # Ждём перед следующей итерацией
            await asyncio.sleep(self.interval_hours * 3600)
    
    async def _cleanup(self):
        """Выполнить очистку"""
        logger.info("🧹 CleanupWorker: очистка старых событий")
        
        await self.sync_service.sync_repo.cleanup_old_events(
            days=self.retention_days
        )
        
        logger.info("✅ CleanupWorker: очистка завершена")
    
    async def cleanup_now(self):
        """Принудительно запустить очистку сейчас"""
        logger.info("⚡ CleanupWorker: принудительная очистка")
        await self._cleanup()
