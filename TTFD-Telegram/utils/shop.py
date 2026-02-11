"""
Утилиты для работы с магазином
"""

import json
import os
from config import SHOP_FILE

def load_shop():
    """Загрузить магазин"""
    os.makedirs('data', exist_ok=True)
    if os.path.exists(SHOP_FILE):
        with open(SHOP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Создаём дефолтный магазин
    default_shop = {
        'items': [
            {
                'id': 1,
                'name': '🎨 Кастомный цвет ника',
                'description': 'Измени цвет своего ника в Discord',
                'price': 1000,
                'type': 'cosmetic'
            },
            {
                'id': 2,
                'name': '⭐ Бустер XP (x2)',
                'description': 'Удвоенный XP на 24 часа',
                'price': 500,
                'type': 'booster'
            },
            {
                'id': 3,
                'name': '💎 Премиум статус',
                'description': 'Премиум статус на 30 дней',
                'price': 5000,
                'type': 'premium'
            },
            {
                'id': 4,
                'name': '🎭 Кастомная роль',
                'description': 'Создай свою уникальную роль',
                'price': 2500,
                'type': 'role'
            },
            {
                'id': 5,
                'name': '🔥 Огненный эффект',
                'description': 'Огненный эффект для аватара',
                'price': 1500,
                'type': 'cosmetic'
            }
        ]
    }
    
    with open(SHOP_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_shop, f, indent=2, ensure_ascii=False)
    
    return default_shop

def save_shop(shop_data):
    """Сохранить магазин"""
    with open(SHOP_FILE, 'w', encoding='utf-8') as f:
        json.dump(shop_data, f, indent=2, ensure_ascii=False)

def get_shop_items():
    """Получить все предметы магазина"""
    shop_data = load_shop()
    return shop_data['items']

def get_item_by_id(item_id):
    """Получить предмет по ID"""
    shop_data = load_shop()
    for item in shop_data['items']:
        if item['id'] == item_id:
            return item
    return None

def add_item(name, description, price, item_type='cosmetic'):
    """Добавить предмет в магазин"""
    shop_data = load_shop()
    
    new_id = max([item['id'] for item in shop_data['items']], default=0) + 1
    
    shop_data['items'].append({
        'id': new_id,
        'name': name,
        'description': description,
        'price': price,
        'type': item_type
    })
    
    save_shop(shop_data)
    return new_id

def remove_item(item_id):
    """Удалить предмет из магазина"""
    shop_data = load_shop()
    shop_data['items'] = [item for item in shop_data['items'] if item['id'] != item_id]
    save_shop(shop_data)
    return True
