# ⚡ Быстрая настройка PostgreSQL

## 3 простых шага:

### 1️⃣ Создай базу данных на Render

```
https://dashboard.render.com
→ New + → PostgreSQL
→ Name: ttfd-database
→ Plan: Free
→ Create Database
```

### 2️⃣ Скопируй DATABASE_URL

```
Открой созданную БД
→ Connections
→ Скопируй "Internal Database URL"
```

### 3️⃣ Добавь в Web Service

```
Открой свой Web Service (ttfd-bot)
→ Environment
→ Add Environment Variable
→ Key: DATABASE_URL
→ Value: (вставь скопированный URL)
→ Save Changes
```

### 4️⃣ Загрузи код на GitHub

```bash
cd C:\Users\brawl\OneDrive\Desktop\папки\TTFD-Website
git add .
git commit -m "Add PostgreSQL support"
git push
```

## ✅ Готово!

Render автоматически:
- Установит psycopg2
- Создаст таблицы
- Начнёт использовать PostgreSQL

Данные больше не будут теряться! 🎉

## 🔍 Проверка

Смотри логи в Render Dashboard:

✅ **Успешно:**
```
✅ Таблицы PostgreSQL инициализированы
✅ Используется PostgreSQL
```

❌ **Ошибка:**
```
⚠️ Используется JSON файл
```

Если ошибка - проверь что DATABASE_URL добавлен правильно.

---

Подробная инструкция: `SETUP_POSTGRESQL.md`
