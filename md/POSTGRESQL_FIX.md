# 🔧 PostgreSQL Compatibility Fix

## Проблема
На production (Render) возникала ошибка:
```
AttributeError: 'PostgresDatabase' object has no attribute 'accounts'
```

Код использовал `db.accounts.get('accounts', {}).values()` для получения списка аккаунтов, что работает только с JSON базой, но не с PostgreSQL.

## Решение

### 1. Добавлен универсальный метод `get_all_accounts()`

**В `database_postgres.py`:**
```python
def get_all_accounts(self):
    """Получить все аккаунты"""
    conn = self.get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM accounts ORDER BY created_at DESC")
    accounts = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return [dict(acc) for acc in accounts]
```

**В `database.py`:**
```python
def get_all_accounts(self):
    """Получить все аккаунты"""
    all_accounts = list(self.accounts.get('accounts', {}).values())
    all_accounts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return all_accounts
```

### 2. Обновлены маршруты в `web.py`

**Маршрут `/users`:**
```python
all_users = db.get_all_accounts()  # Вместо db.accounts.get()
```

**Маршрут `/api/user_by_discord/<discord_id>`:**
```python
all_accounts = db.get_all_accounts()  # Вместо db.accounts.get()
for acc in all_accounts:
    if str(acc.get('discord_id')) == str(discord_id):
        # ...
```

### 3. Исправлена структура HTML в `settings_premium.html`

- Убран лишний закрывающий `</div>` после `<div class="container">`
- Убран дублирующий `</div>` в блоке персонализации профиля

## Результат

✅ Код теперь работает одинаково с JSON и PostgreSQL базами
✅ Страница `/users` больше не вызывает ошибок
✅ API `/api/user_by_discord/<discord_id>` работает корректно
✅ HTML структура валидна

## Коммит
```
Fix PostgreSQL compatibility: add get_all_accounts() method and fix settings HTML structure
```
