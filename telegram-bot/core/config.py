"""
Application configuration
"""
import os
from typing import List
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()


class Config:
    """Конфигурация приложения"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_ADMIN_IDS: List[str] = [
        id.strip() 
        for id in os.getenv('TELEGRAM_ADMIN_IDS', '').split(',') 
        if id.strip()
    ]
    
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/ttfd')
    
    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Discord (опционально)
    DISCORD_BOT_TOKEN: str = os.getenv('DISCORD_BOT_TOKEN', '')
    DISCORD_GUILD_ID: str = os.getenv('DISCORD_GUILD_ID', '')
    
    # AI (опционально)
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    
    # Настройки наград
    DAILY_REWARD_XP: int = 100
    DAILY_REWARD_COINS: int = 50
    DAILY_COOLDOWN_HOURS: int = 24
    
    # Настройки магазина
    SHOP_ENABLED: bool = True
    
    # Кэширование
    CACHE_TTL_USER_PROFILE: int = 300  # 5 минут
    CACHE_TTL_LEADERBOARD: int = 60    # 1 минута
    CACHE_TTL_SHOP: int = 600          # 10 минут
    
    @classmethod
    def validate(cls):
        """Валидация конфигурации"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен!")
        
        if not cls.TELEGRAM_ADMIN_IDS:
            print("⚠️  TELEGRAM_ADMIN_IDS не установлен - админ-функции недоступны")
        
        print("✅ Конфигурация загружена")
        if cls.TELEGRAM_ADMIN_IDS:
            print(f"   Админы: {', '.join(cls.TELEGRAM_ADMIN_IDS)}")
        print(f"   Database: {cls.DATABASE_URL.split('@')[1] if '@' in cls.DATABASE_URL else 'local'}")
        print(f"   Redis: {cls.REDIS_URL}")


# Валидируем при импорте
Config.validate()
