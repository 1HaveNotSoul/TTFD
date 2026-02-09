"""
AI Service - интеграция с OpenAI
"""
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Проверяем наличие openai
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️  OpenAI не установлен. AI-функции недоступны.")


class AIService:
    """Сервис для работы с AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.enabled = OPENAI_AVAILABLE and bool(self.api_key)
        
        if self.enabled:
            openai.api_key = self.api_key
            logger.info("✅ AI Service инициализирован")
        else:
            logger.warning("⚠️  AI Service отключён (нет API ключа или библиотеки)")
    
    async def generate_support_response(
        self,
        ticket_subject: str,
        ticket_category: str
    ) -> Optional[str]:
        """
        Сгенерировать черновик ответа на тикет
        
        Args:
            ticket_subject: Текст тикета
            ticket_category: Категория тикета
        
        Returns:
            Черновик ответа или None
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""
Ты - помощник службы поддержки Telegram-бота TTFD.

Категория тикета: {ticket_category}
Вопрос пользователя: {ticket_subject}

Напиши краткий и полезный ответ на русском языке (максимум 200 слов).
Будь вежливым и профессиональным.
"""
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - помощник службы поддержки."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            draft = response.choices[0].message.content.strip()
            logger.info(f"✅ AI сгенерировал черновик ответа ({len(draft)} символов)")
            
            return draft
        
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            return None
    
    async def analyze_user_behavior(
        self,
        user_stats: dict
    ) -> Optional[dict]:
        """
        Анализ поведения пользователя
        
        Args:
            user_stats: Статистика пользователя
        
        Returns:
            Анализ или None
        """
        if not self.enabled:
            return None
        
        try:
            # Простой анализ без AI (для экономии токенов)
            analysis = {
                'activity_level': 'high' if user_stats.get('total_games', 0) > 50 else 'medium' if user_stats.get('total_games', 0) > 10 else 'low',
                'engagement': 'active' if user_stats.get('last_active_days', 999) < 7 else 'inactive',
                'risk_level': 'low'  # Можно добавить логику определения риска
            }
            
            return analysis
        
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            return None
    
    async def generate_quiz_question(self, difficulty: str = 'medium') -> Optional[dict]:
        """
        Сгенерировать вопрос для квиза
        
        Args:
            difficulty: Сложность (easy, medium, hard)
        
        Returns:
            Вопрос с вариантами ответов или None
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""
Создай интересный вопрос для квиза на русском языке.
Сложность: {difficulty}
Тема: общие знания, наука, технологии или культура

Формат ответа (JSON):
{{
    "question": "Текст вопроса?",
    "options": ["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"],
    "correct": 0
}}

где correct - индекс правильного ответа (0-3)
"""
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - генератор вопросов для квиза."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            import json
            quiz_data = json.loads(response.choices[0].message.content.strip())
            
            logger.info(f"✅ AI сгенерировал вопрос квиза")
            
            return quiz_data
        
        except Exception as e:
            logger.error(f"❌ Ошибка генерации вопроса: {e}")
            return None
    
    async def moderate_content(self, text: str) -> dict:
        """
        Модерация контента
        
        Args:
            text: Текст для проверки
        
        Returns:
            Результат модерации
        """
        if not self.enabled:
            return {'flagged': False, 'categories': {}}
        
        try:
            response = await openai.Moderation.acreate(input=text)
            result = response.results[0]
            
            return {
                'flagged': result.flagged,
                'categories': result.categories.to_dict() if hasattr(result.categories, 'to_dict') else {}
            }
        
        except Exception as e:
            logger.error(f"❌ Ошибка модерации: {e}")
            return {'flagged': False, 'categories': {}}
