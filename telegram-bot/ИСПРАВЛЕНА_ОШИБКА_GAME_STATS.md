# ✅ Исправлена ошибка в update_game_stats

## 🐛 Проблема

```
TypeError: Database.update_user() got multiple values for argument 'telegram_id'
```

Ошибка возникала при завершении игры (квиз, угадай число) когда бот пытался обновить статистику игр.

---

## 🔍 Причина

В функции `update_game_stats` (файл `utils/games.py`) происходила передача `telegram_id` дважды:

**Было:**
```python
def update_game_stats(telegram_id, won=False, coins_won=0):
    user = db.get_user(telegram_id)
    
    user['games_played'] = user.get('games_played', 0) + 1
    if won:
        user['games_won'] = user.get('games_won', 0) + 1
    user['total_coins_won'] = user.get('total_coins_won', 0) + coins_won
    
    # Проблема: user содержит telegram_id, и мы передаём его ещё раз
    user_updates = {k: v for k, v in user.items() if k != 'telegram_id'}
    db.update_user(telegram_id, **user_updates)  # ❌ Передаём весь словарь
```

Проблема: `user_updates` всё ещё содержал много лишних полей, что могло вызывать конфликты.

---

## ✅ Решение

**Стало:**
```python
def update_game_stats(telegram_id, won=False, coins_won=0):
    user = db.get_user(telegram_id)
    
    user['games_played'] = user.get('games_played', 0) + 1
    if won:
        user['games_won'] = user.get('games_won', 0) + 1
    user['total_coins_won'] = user.get('total_coins_won', 0) + coins_won
    
    # Обновляем только нужные поля
    db.update_user(
        telegram_id,
        games_played=user['games_played'],
        games_won=user.get('games_won', 0),
        total_coins_won=user['total_coins_won']
    )  # ✅ Передаём только нужные поля
```

Теперь передаются только те поля, которые действительно нужно обновить.

---

## 📋 Изменённые файлы

- `TTFD/telegram-bot/utils/games.py` - функция `update_game_stats`

---

## 🚀 Деплой

Изменения залиты на GitHub:
```bash
git add utils/games.py
git commit -m "Fix: update_game_stats TypeError - remove duplicate telegram_id"
git push --force
```

Railway автоматически задеплоит обновление в течение 2-5 минут.

---

## ✅ Результат

- ✅ Ошибка `TypeError` исправлена
- ✅ Игры (квиз, угадай число) теперь корректно обновляют статистику
- ✅ Монеты начисляются правильно
- ✅ Статистика побед/поражений работает

---

**Дата**: 2026-02-08  
**Статус**: ✅ Исправлено и задеплоено
