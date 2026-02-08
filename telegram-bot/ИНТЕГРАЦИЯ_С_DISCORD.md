# 🔗 Интеграция Telegram бота с Discord

## Как это работает

Telegram бот может синхронизироваться с Discord ботом через общую базу данных.

## Варианты интеграции

### Вариант 1: Общая база данных (PostgreSQL)

**Преимущества:**
- Реальная синхронизация
- Общие XP, монеты, ранги
- Единая система

**Как реализовать:**
1. Мигрировать обе БД на PostgreSQL
2. Использовать одну БД для обоих ботов
3. Синхронизировать через `discord_id` и `telegram_id`

### Вариант 2: API между ботами

**Преимущества:**
- Независимые боты
- Легко масштабировать
- Можно использовать разные БД

**Как реализовать:**
1. Создать REST API на Flask/FastAPI
2. Discord бот отправляет данные в API
3. Telegram бот получает данные из API

### Вариант 3: Webhook уведомления

**Преимущества:**
- Реальное время
- Уведомления о событиях
- Легко настроить

**Как реализовать:**
1. Discord бот отправляет webhook при событиях
2. Telegram бот получает уведомления
3. Обновляет свою БД

## Текущая реализация

Сейчас реализована **привязка аккаунтов**:

```python
# Пользователь привязывает Discord
/link 123456789012345678

# В БД сохраняется
{
  "telegram_id": "123456789",
  "discord_id": "123456789012345678",
  ...
}
```

## Следующие шаги

### 1. Синхронизация XP

```python
# В Discord боте при начислении XP
def add_xp(discord_id, amount):
    # Добавляем XP в Discord БД
    discord_db.add_xp(discord_id, amount)
    
    # Находим привязанный Telegram аккаунт
    telegram_id = get_linked_telegram(discord_id)
    if telegram_id:
        # Синхронизируем с Telegram БД
        telegram_db.add_xp(telegram_id, amount)
```

### 2. Синхронизация монет

```python
# Аналогично XP
def add_coins(discord_id, amount):
    discord_db.add_coins(discord_id, amount)
    telegram_id = get_linked_telegram(discord_id)
    if telegram_id:
        telegram_db.add_coins(telegram_id, amount)
```

### 3. Уведомления о рангах

```python
# При повышении ранга в Discord
async def on_rank_up(discord_id, new_rank):
    telegram_id = get_linked_telegram(discord_id)
    if telegram_id:
        # Отправляем уведомление в Telegram
        await telegram_bot.send_message(
            telegram_id,
            f"🎉 Поздравляем! Ты достиг ранга {new_rank}!"
        )
```

## Пример полной интеграции

### Discord бот (TTFD-Discord/main.py)

```python
import requests

TELEGRAM_API_URL = "http://localhost:5000/api"

def sync_with_telegram(discord_id, action, data):
    """Синхронизация с Telegram ботом"""
    try:
        response = requests.post(
            f"{TELEGRAM_API_URL}/sync",
            json={
                "discord_id": discord_id,
                "action": action,
                "data": data
            }
        )
        return response.json()
    except:
        return None

# При начислении XP
def add_xp(user_id, amount):
    # Discord БД
    db.add_xp(user_id, amount)
    
    # Синхронизация с Telegram
    sync_with_telegram(user_id, "add_xp", {"amount": amount})
```

### Telegram бот (TTFD-Telegram/api.py)

```python
from flask import Flask, request, jsonify
from database import db

app = Flask(__name__)

@app.route('/api/sync', methods=['POST'])
def sync():
    """API для синхронизации с Discord"""
    data = request.json
    discord_id = data['discord_id']
    action = data['action']
    
    # Находим привязанный Telegram аккаунт
    telegram_id = find_telegram_by_discord(discord_id)
    
    if not telegram_id:
        return jsonify({"error": "Not linked"}), 404
    
    if action == "add_xp":
        db.add_xp(telegram_id, data['data']['amount'])
    elif action == "add_coins":
        db.add_coins(telegram_id, data['data']['amount'])
    
    return jsonify({"success": True})

def find_telegram_by_discord(discord_id):
    """Найти Telegram ID по Discord ID"""
    for user in db.get_all_users():
        if user.get('discord_id') == str(discord_id):
            return user['telegram_id']
    return None
```

## Рекомендации

1. **Начни с простого** - сначала реализуй привязку аккаунтов
2. **Используй PostgreSQL** - для продакшена лучше использовать реальную БД
3. **Добавь API** - создай REST API для синхронизации
4. **Webhook уведомления** - для реального времени
5. **Обработка ошибок** - что делать если один бот недоступен?

## Безопасность

- Используй API ключи для защиты API
- Валидируй все данные
- Логируй все синхронизации
- Обрабатывай ошибки сети

## Тестирование

1. Привяжи аккаунт через `/link`
2. Начисли XP в Discord
3. Проверь что XP появился в Telegram
4. Проверь уведомления

---

**Статус:** Базовая привязка реализована  
**Следующий шаг:** Реализовать синхронизацию XP и монет
