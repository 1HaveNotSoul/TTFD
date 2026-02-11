"""
Redis cache implementation
"""
import json
from typing import Optional, Any
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  redis не установлен - кэширование отключено")


class RedisCache:
    """Redis кэш"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.enabled = REDIS_AVAILABLE
    
    async def connect(self):
        """Подключиться к Redis"""
        if not self.enabled:
            print("⚠️  Redis кэш отключён (библиотека не установлена)")
            return
        
        try:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            print("✅ Подключено к Redis")
        except Exception as e:
            print(f"⚠️  Не удалось подключиться к Redis: {e}")
            print("   Кэширование будет отключено")
            self.enabled = False
    
    async def disconnect(self):
        """Отключиться от Redis"""
        if self.redis:
            await self.redis.close()
            print("✅ Отключено от Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        if not self.enabled or not self.redis:
            return None
        
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"⚠️  Ошибка чтения из Redis: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Сохранить значение в кэш"""
        if not self.enabled or not self.redis:
            return
        
        try:
            await self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"⚠️  Ошибка записи в Redis: {e}")
    
    async def delete(self, key: str):
        """Удалить значение из кэша"""
        if not self.enabled or not self.redis:
            return
        
        try:
            await self.redis.delete(key)
        except Exception as e:
            print(f"⚠️  Ошибка удаления из Redis: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Инвалидировать по паттерну"""
        if not self.enabled or not self.redis:
            return
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            print(f"⚠️  Ошибка инвалидации паттерна: {e}")


class MemoryCache:
    """Простой in-memory кэш (fallback если Redis недоступен)"""
    
    def __init__(self):
        self.cache = {}
        self.enabled = True
        print("✅ Используется MemoryCache (fallback)")
    
    async def connect(self):
        """Заглушка для совместимости"""
        pass
    
    async def disconnect(self):
        """Заглушка для совместимости"""
        pass
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить из памяти"""
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Сохранить в память (TTL игнорируется)"""
        self.cache[key] = value
    
    async def delete(self, key: str):
        """Удалить из памяти"""
        self.cache.pop(key, None)
    
    async def invalidate_pattern(self, pattern: str):
        """Инвалидировать по паттерну"""
        # Простая реализация для MemoryCache
        pattern = pattern.replace('*', '')
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
