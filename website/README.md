# 🌐 TTFD Website

Веб-сайт TTFD с профилями, кастомизацией, магазином и Discord OAuth авторизацией.

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка

Создай файл `.env` на основе `.env.example`:

```env
# Flask
SECRET_KEY=твой_секретный_ключ
PORT=5000

# Discord OAuth
DISCORD_CLIENT_ID=твой_client_id
DISCORD_CLIENT_SECRET=твой_client_secret
DISCORD_REDIRECT_URI=https://ttfd.onrender.com/auth/discord/callback
```

**Где взять Discord OAuth данные:**
- https://discord.com/developers/applications
- Выбери приложение → OAuth2 → General
- Client ID и Client Secret
- Добавь Redirect URI в списке разрешённых

### 3. Запуск

```bash
python main.py
```

Сайт будет доступен на http://localhost:5000

## 📋 Возможности

### Для пользователей:
- ✅ **Discord OAuth** - Вход через Discord
- 🎨 **Кастомизация** - Настройка темы, цветов, фона
- 👤 **Профиль** - Личная страница с музыкой и информацией
- ⚙️ **Настройки** - Управление аккаунтом
- 🛒 **Магазин** - Покупка товаров и услуг

### Технические:
- Flask веб-фреймворк
- Discord OAuth 2.0
- JSON/PostgreSQL база данных
- Адаптивный дизайн
- Темная тема

## 📁 Структура проекта

```
TTFD-Website/
├── app.py                 # Flask приложение и роуты
├── main.py                # Точка входа
├── config.py              # Конфигурация
├── discord_oauth.py       # Discord OAuth логика
├── database.py            # База данных (JSON)
├── database_postgres.py   # База данных (PostgreSQL)
├── static/                # CSS, JS, изображения
│   ├── css/
│   ├── js/
│   └── фотографии/
└── templates/             # HTML шаблоны
    ├── base.html
    ├── index.html
    ├── login.html
    ├── profile.html
    ├── settings.html
    ├── customize.html
    └── shop.html
```

## 🔧 Настройка

### База данных

По умолчанию используется JSON файл (`accounts.json`).

Для PostgreSQL добавь в `.env`:

```env
DATABASE_URL=postgresql://user:password@host/database
```

### Discord OAuth

1. Создай приложение на https://discord.com/developers/applications
2. OAuth2 → Redirects → Добавь `https://твой-домен.com/auth/discord/callback`
3. OAuth2 → General → Скопируй Client ID и Client Secret
4. Добавь в `.env`

## 🚀 Деплой на Render

1. Создай Web Service на https://render.com
2. Подключи GitHub репозиторий
3. Настрой Environment Variables:
   - `SECRET_KEY`
   - `DISCORD_CLIENT_ID`
   - `DISCORD_CLIENT_SECRET`
   - `DISCORD_REDIRECT_URI`
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python main.py`

## 🤖 Discord Бот

Discord бот теперь в отдельном проекте: **TTFD-Discord**

Это позволяет:
- Запускать бота и сайт независимо
- Деплоить на разные сервера
- Избежать конфликтов зависимостей

## 📝 Разработка

### Добавление нового роута

```python
@app.route('/mypage')
def my_page():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login'))
    return render_template('mypage.html', user=current_user)
```

### Обновление темы

Все стили в `static/css/`, темы управляются через `theme-engine.js`.

## 🐛 Troubleshooting

### OAuth не работает

- Проверь что DISCORD_CLIENT_ID и DISCORD_CLIENT_SECRET правильные
- Проверь что DISCORD_REDIRECT_URI совпадает с настройками в Discord Developer Portal
- Проверь что redirect URI добавлен в список разрешённых

### Сайт не запускается

- Проверь что установлены все зависимости
- Проверь что PORT не занят другим приложением
- Проверь логи на наличие ошибок

## 📄 Лицензия

MIT

---

**Последнее обновление:** 30.01.2026  
**Discord Бот:** См. проект TTFD-Discord
