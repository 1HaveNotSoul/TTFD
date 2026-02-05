# Единая цветовая схема бота - Чёрно-Красный градиент

import discord

# Основные цвета темы
class BotTheme:
    """Чёрно-красная цветовая схема бота"""
    
    # Основные цвета
    PRIMARY = 0x1a0000      # Очень тёмный красный (почти чёрный)
    SECONDARY = 0xff0000    # Ярко-красный
    DARK = 0x0d0d0d         # Почти чёрный
    LIGHT_RED = 0xff4444    # Светло-красный
    BLOOD_RED = 0x8b0000    # Кроваво-красный
    
    # Цвета для разных типов сообщений
    SUCCESS = 0x00ff00      # Зелёный для успеха
    ERROR = 0xff0000        # Красный для ошибок
    WARNING = 0xff6600      # Оранжево-красный для предупреждений
    INFO = 0xff4444         # Светло-красный для информации
    
    # Градиентные цвета (от тёмного к светлому)
    GRADIENT = [
        0x0d0d0d,  # Чёрный
        0x1a0000,  # Очень тёмный красный
        0x330000,  # Тёмный красный
        0x660000,  # Средне-тёмный красный
        0x8b0000,  # Кроваво-красный
        0xcc0000,  # Красный
        0xff0000,  # Ярко-красный
        0xff4444,  # Светло-красный
    ]
    
    # Эмодзи для разных типов сообщений
    EMOJI = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'fire': '🔥',
        'star': '⭐',
        'crown': '👑',
        'game': '🎮',
        'money': '💰',
        'xp': '⚡',
        'rank': '🏆',
        'ticket': '🎫',
        'music': '🎵',
        'shop': '🛒',
        'achievement': '🏅',
    }
    
    @staticmethod
    def get_gradient_color(index=0):
        """Получить цвет из градиента по индексу"""
        return BotTheme.GRADIENT[index % len(BotTheme.GRADIENT)]
    
    @staticmethod
    def create_embed(title, description=None, color=None, embed_type='info'):
        """
        Создать embed с единым стилем
        
        Args:
            title: Заголовок
            description: Описание (опционально)
            color: Цвет (опционально, по умолчанию из типа)
            embed_type: Тип embed ('success', 'error', 'warning', 'info', 'game', 'profile')
        
        Returns:
            discord.Embed
        """
        # Определяем цвет по типу
        color_map = {
            'success': BotTheme.SUCCESS,
            'error': BotTheme.ERROR,
            'warning': BotTheme.WARNING,
            'info': BotTheme.INFO,
            'game': BotTheme.BLOOD_RED,
            'profile': BotTheme.LIGHT_RED,
            'shop': BotTheme.SECONDARY,
            'achievement': BotTheme.BLOOD_RED,
            'music': BotTheme.LIGHT_RED,
            'ticket': BotTheme.PRIMARY,
            'rank': BotTheme.BLOOD_RED,
        }
        
        if color is None:
            color = color_map.get(embed_type, BotTheme.INFO)
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=color
        )
        
        return embed
    
    @staticmethod
    def create_game_embed(title, description=None):
        """Создать embed для игр"""
        return BotTheme.create_embed(title, description, embed_type='game')
    
    @staticmethod
    def create_profile_embed(title, description=None):
        """Создать embed для профиля"""
        return BotTheme.create_embed(title, description, embed_type='profile')
    
    @staticmethod
    def create_shop_embed(title, description=None):
        """Создать embed для магазина"""
        return BotTheme.create_embed(title, description, embed_type='shop')
    
    @staticmethod
    def create_success_embed(title, description=None):
        """Создать embed для успеха"""
        return BotTheme.create_embed(title, description, embed_type='success')
    
    @staticmethod
    def create_error_embed(title, description=None):
        """Создать embed для ошибки"""
        return BotTheme.create_embed(title, description, embed_type='error')
    
    @staticmethod
    def create_warning_embed(title, description=None):
        """Создать embed для предупреждения"""
        return BotTheme.create_embed(title, description, embed_type='warning')


# Быстрые функции для создания embed
def game_embed(title, description=None):
    """Быстрое создание игрового embed"""
    return BotTheme.create_game_embed(title, description)

def profile_embed(title, description=None):
    """Быстрое создание профильного embed"""
    return BotTheme.create_profile_embed(title, description)

def shop_embed(title, description=None):
    """Быстрое создание магазинного embed"""
    return BotTheme.create_shop_embed(title, description)

def success_embed(title, description=None):
    """Быстрое создание успешного embed"""
    return BotTheme.create_success_embed(title, description)

def error_embed(title, description=None):
    """Быстрое создание ошибочного embed"""
    return BotTheme.create_error_embed(title, description)

def warning_embed(title, description=None):
    """Быстрое создание предупреждающего embed"""
    return BotTheme.create_warning_embed(title, description)


# Тестирование
if __name__ == "__main__":
    print("="*70)
    print("ЦВЕТОВАЯ СХЕМА БОТА - ЧЁРНО-КРАСНЫЙ ГРАДИЕНТ")
    print("="*70)
    print(f"\nОсновные цвета:")
    print(f"  PRIMARY (тёмный красный):  #{BotTheme.PRIMARY:06x}")
    print(f"  SECONDARY (ярко-красный):  #{BotTheme.SECONDARY:06x}")
    print(f"  DARK (чёрный):             #{BotTheme.DARK:06x}")
    print(f"  LIGHT_RED (светло-красный):#{BotTheme.LIGHT_RED:06x}")
    print(f"  BLOOD_RED (кроваво-красный):#{BotTheme.BLOOD_RED:06x}")
    
    print(f"\nГрадиент (8 оттенков):")
    for i, color in enumerate(BotTheme.GRADIENT):
        print(f"  {i+1}. #{color:06x}")
    
    print(f"\nТипы embed:")
    print(f"  success:     Зелёный")
    print(f"  error:       Красный")
    print(f"  warning:     Оранжево-красный")
    print(f"  info:        Светло-красный")
    print(f"  game:        Кроваво-красный")
    print(f"  profile:     Светло-красный")
    print(f"  shop:        Ярко-красный")
    print(f"  achievement: Кроваво-красный")
    
    print("\n" + "="*70)
    print("✅ Модуль theme.py готов к использованию!")
    print("="*70)
