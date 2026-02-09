# ⚡ БЫСТРЫЙ СТАРТ: КОДЫ ПРИВЯЗКИ

**Для пользователей:** Как быстро привязать Discord к Telegram

---

## 🎯 ДЛЯ ПОЛЬЗОВАТЕЛЕЙ

### 1. В Telegram боте

```
/linkcode
```

Получишь код: `ABC123`

### 2. В Discord боте

```
/link ABC123
```

### 3. Готово! ✅

Баланс синхронизирован между Telegram и Discord!

**Время:** 30 секунд вместо 5 минут

---

## 🔧 ДЛЯ РАЗРАБОТЧИКА

### Интеграция

**1. Telegram Bot (`main.py`):**

```python
from handlers.link_code import linkcode_command, linkcode_callback, mycodes_command

app.add_handler(CommandHandler("linkcode", linkcode_command))
app.add_handler(CommandHandler("mycodes", mycodes_command))
app.add_handler(CallbackQueryHandler(linkcode_callback, pattern="^linkcode_new$"))
```

**2. Discord Bot (`bot.py`):**

```python
from link_code_commands import setup_link_code_commands

# В on_ready
await setup_link_code_commands(bot, db)
```

**3. Создать таблицу:**

```sql
CREATE TABLE link_codes (
    code TEXT PRIMARY KEY,
    telegram_id TEXT NOT NULL,
    discord_id TEXT,
    platform TEXT NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP
);
```

**4. Деплой:**

```bash
git add .
git commit -m "Добавлена система кодов привязки"
git push
```

---

## 📊 НОВЫЕ КОМАНДЫ

**Telegram:**
- `/linkcode` - сгенерировать код
- `/mycodes` - мои коды

**Discord:**
- `/link <код>` - привязать через код
- `/checklink` - проверить привязку

---

**Готово!** 🎉

Пользователи смогут привязать аккаунты за 30 секунд.
