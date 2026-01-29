# Telegram бот для резервного хранения данных
import os
import json
import asyncio
from datetime import datetime
import aiohttp

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_BACKUP_CHAT_ID')  # ID чата для бэкапов

class TelegramBackup:
    """Telegram бот для резервного копирования данных"""
    
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        if not self.token:
            print("⚠️ TELEGRAM_BOT_TOKEN не установлен")
        if not self.chat_id:
            print("⚠️ TELEGRAM_BACKUP_CHAT_ID не установлен")
    
    async def send_message(self, text):
        """Отправить сообщение в Telegram"""
        if not self.token or not self.chat_id:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                data = {
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': 'HTML'
                }
                async with session.post(url, json=data) as response:
                    return response.status == 200
        except Exception as e:
            print(f"❌ Ошибка отправки в Telegram: {e}")
            return False
    
    async def send_document(self, file_path, caption=""):
        """Отправить файл в Telegram"""
        if not self.token or not self.chat_id:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendDocument"
                
                with open(file_path, 'rb') as file:
                    form = aiohttp.FormData()
                    form.add_field('chat_id', self.chat_id)
                    form.add_field('document', file, filename=os.path.basename(file_path))
                    if caption:
                        form.add_field('caption', caption)
                    
                    async with session.post(url, data=form) as response:
                        return response.status == 200
        except Exception as e:
            print(f"❌ Ошибка отправки файла в Telegram: {e}")
            return False
    
    async def backup_data(self, data, backup_name="backup"):
        """Создать бэкап данных"""
        if not self.token or not self.chat_id:
            print("⚠️ Telegram бэкап не настроен")
            return False
        
        try:
            # Сохраняем во временный файл
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{backup_name}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Отправляем в Telegram
            caption = f"🔄 Бэкап: {backup_name}\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            success = await self.send_document(filename, caption)
            
            # Удаляем временный файл
            os.remove(filename)
            
            if success:
                print(f"✅ Бэкап {backup_name} отправлен в Telegram")
            
            return success
        except Exception as e:
            print(f"❌ Ошибка создания бэкапа: {e}")
            return False
    
    async def get_latest_backup(self, backup_name="backup"):
        """Получить последний бэкап из Telegram"""
        if not self.token or not self.chat_id:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Получаем последние сообщения
                url = f"{self.base_url}/getUpdates"
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    
                    # Ищем последний файл с нужным именем
                    for update in reversed(data.get('result', [])):
                        message = update.get('message', {})
                        document = message.get('document', {})
                        
                        if document and backup_name in document.get('file_name', ''):
                            file_id = document['file_id']
                            
                            # Получаем файл
                            file_url = f"{self.base_url}/getFile?file_id={file_id}"
                            async with session.get(file_url) as file_response:
                                file_data = await file_response.json()
                                file_path = file_data['result']['file_path']
                                
                                # Скачиваем файл
                                download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                                async with session.get(download_url) as download_response:
                                    content = await download_response.text()
                                    return json.loads(content)
            
            return None
        except Exception as e:
            print(f"❌ Ошибка получения бэкапа: {e}")
            return None
    
    async def send_stats(self, stats_text):
        """Отправить статистику в Telegram"""
        return await self.send_message(f"📊 <b>Статистика</b>\n\n{stats_text}")
    
    async def send_alert(self, alert_text):
        """Отправить уведомление в Telegram"""
        return await self.send_message(f"🚨 <b>Уведомление</b>\n\n{alert_text}")

# Глобальный экземпляр
telegram_backup = TelegramBackup()

# Функция для автоматического бэкапа
async def auto_backup_to_telegram(db):
    """Автоматический бэкап в Telegram каждые 6 часов"""
    while True:
        try:
            # Получаем данные из БД
            if hasattr(db, 'data'):
                # JSON база
                await telegram_backup.backup_data(db.data, "user_data")
                await telegram_backup.backup_data(db.accounts, "accounts")
            else:
                # PostgreSQL база - делаем дамп
                users = db.get_leaderboard(1000)  # Все пользователи
                await telegram_backup.backup_data({'users': users}, "postgres_backup")
            
            print("✅ Автоматический бэкап в Telegram выполнен")
        except Exception as e:
            print(f"❌ Ошибка автобэкапа: {e}")
        
        # Ждём 6 часов
        await asyncio.sleep(6 * 60 * 60)
