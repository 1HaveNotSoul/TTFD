# 🚀 Deployment Guide - TTFD Project

Полное руководство по деплою всех компонентов TTFD на Render.com

## 📋 Содержание

1. [Подготовка](#подготовка)
2. [PostgreSQL Database](#postgresql-database)
3. [Website (Web Service)](#website-web-service)
4. [Discord Bot (Background Worker)](#discord-bot-background-worker)
5. [Cleaner (Standalone)](#cleaner-standalone)
6. [Проверка работы](#проверка-работы)
7. [Troubleshooting](#troubleshooting)

## 🔧 Подготовка

### 1. GitHub Repository

```bash
# Создайте репозиторий на GitHub
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/TTFD.git
git push -u origin main
```

### 2. Discord Developer Portal

1. Перейдите на https://discord.com/developers/applications
2. Создайте новое приложение (или используйте существующее)

**Для Discord Bot:**
- Bot → Reset Token → Скопируйте токен
- Bot → Privileged Gateway Intents → Включите все

**Для Website OAuth:**
- OAuth2 → General → Скопируйте Client ID и Client Secret
- OAuth2 → Redirects → Добавьте: `https://your-app.onrender.com/auth/discord/callback`

### 3. Render.com Account

Зарегистрируйтесь на https://render.com

## 🗄️ PostgreSQL Database

### Создание базы данных

1. Dashboard → New → PostgreSQL
2. Настройки:
   - **Name:** `ttfd-database`
   - **Database:** `ttfd`
   - **User:** `ttfd_user`
   - **Region:** Frankfurt (EU Central)
   - **Plan:** Free
3. Create Database

### Получение URL

После создания:
1. Откройте базу данных
2. Скопируйте **Internal Database URL**
3. Формат: `postgresql://user:password@host/database`

**Важно:** Используйте Internal URL для сервисов на Render!

## 🌐 Website (Web Service)

### Создание сервиса

1. Dashboard → New → Web Service
2. Connect Repository: выберите ваш GitHub репозиторий
3. Настройки:

```yaml
Name: ttfd-website
Region: Frankfurt (EU Central)
Branch: main
Root Directory: website
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python main.py
Plan: Free
```

### Environment Variables

Добавьте следующие переменные:

```env
# Flask
SECRET_KEY=your_random_secret_key_here_min_32_chars
PORT=10000

# Discord OAuth
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=https://ttfd-website.onrender.com/auth/discord/callback

# Database
DATABASE_URL=postgresql://user:password@host/database
```

**Генерация SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

### Обновление Redirect URI

После деплоя:
1. Скопируйте URL вашего сайта (например: `https://ttfd-website.onrender.com`)
2. Discord Developer Portal → OAuth2 → Redirects
3. Обновите redirect URI: `https://ttfd-website.onrender.com/auth/discord/callback`
4. Обновите `DISCORD_REDIRECT_URI` в Environment Variables

### Deploy

1. Create Web Service
2. Дождитесь завершения деплоя (5-10 минут)
3. Проверьте логи на наличие ошибок

## 🤖 Discord Bot (Background Worker)

### Создание сервиса

1. Dashboard → New → Background Worker
2. Connect Repository: выберите ваш GitHub репозиторий
3. Настройки:

```yaml
Name: ttfd-discord-bot
Region: Frankfurt (EU Central)
Branch: main
Root Directory: discord-bot
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python main.py
Plan: Free
```

### Environment Variables

```env
# Discord Bot
DISCORD_TOKEN=your_discord_bot_token
GUILD_ID=your_guild_id

# Database (тот же что и для Website)
DATABASE_URL=postgresql://user:password@host/database
```

**Получение GUILD_ID:**
1. Discord → User Settings → Advanced → Developer Mode (включить)
2. Правый клик на сервере → Copy Server ID

### Deploy

1. Create Background Worker
2. Дождитесь завершения деплоя
3. Проверьте логи - бот должен подключиться к Discord

## 🧹 Cleaner (Standalone)

Cleaner не требует деплоя на сервер - это standalone приложение.

### Сборка EXE

```bash
cd cleaner
.\СОБРАТЬ_EXE.bat
```

### Распространение

Готовый файл: `cleaner/dist/TTFD-Cleaner-Menu.exe`

**Способы распространения:**
1. GitHub Releases
2. Discord сервер (файл или ссылка)
3. Website (страница загрузки)
4. Прямая передача

### GitHub Release

```bash
# Создайте тег
git tag -a v1.5.0 -m "TTFD-Cleaner v1.5.0"
git push origin v1.5.0

# Загрузите EXE в GitHub Releases
```

## ✅ Проверка работы

### Website

1. Откройте URL сайта
2. Проверьте главную страницу
3. Попробуйте войти через Discord
4. Проверьте профиль, настройки, кастомизацию

**Тест OAuth:**
```
https://your-site.onrender.com/login
→ Discord OAuth
→ Redirect обратно
→ Профиль создан
```

### Discord Bot

1. Откройте Discord сервер
2. Проверьте что бот онлайн
3. Попробуйте команды:
   ```
   !ping
   !profile
   !help
   ```

**Проверка логов:**
```
Render Dashboard → ttfd-discord-bot → Logs
```

### Database

**Проверка подключения:**
```python
import psycopg2
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("SELECT version();")
print(cur.fetchone())
```

## 🐛 Troubleshooting

### Website не запускается

**Проблема:** Application failed to respond
```
Решение:
1. Проверьте логи на ошибки
2. Убедитесь что PORT=10000
3. Проверьте что app.run использует правильный порт
4. Проверьте requirements.txt
```

**Проблема:** OAuth не работает
```
Решение:
1. Проверьте DISCORD_CLIENT_ID и DISCORD_CLIENT_SECRET
2. Проверьте DISCORD_REDIRECT_URI (должен совпадать с Discord Portal)
3. Убедитесь что redirect URI добавлен в Discord Portal
```

### Discord Bot не подключается

**Проблема:** Bot offline
```
Решение:
1. Проверьте DISCORD_TOKEN (может быть устаревший)
2. Проверьте Privileged Gateway Intents в Discord Portal
3. Проверьте логи на ошибки
```

**Проблема:** Commands not working
```
Решение:
1. Проверьте что бот имеет нужные permissions
2. Проверьте GUILD_ID
3. Попробуйте !ping для проверки
```

### Database ошибки

**Проблема:** Connection refused
```
Решение:
1. Используйте Internal Database URL (не External)
2. Проверьте что DATABASE_URL правильный
3. Проверьте что база данных запущена
```

**Проблема:** Table does not exist
```
Решение:
1. Запустите миграции (если есть)
2. Или база создаст таблицы автоматически при первом запуске
```

### Cleaner проблемы

**Проблема:** Антивирус блокирует
```
Решение:
1. Добавьте в исключения антивируса
2. Это ложное срабатывание на PyInstaller
3. Можно подписать EXE цифровой подписью
```

**Проблема:** EXE не запускается
```
Решение:
1. Запустите от имени администратора
2. Проверьте что все DLL включены
3. Пересоберите с --clean флагом
```

## 🔄 Обновление

### Website и Discord Bot

```bash
# Внесите изменения
git add .
git commit -m "feat: новая функция"
git push origin main

# Render автоматически задеплоит изменения
```

**Ручной деплой:**
```
Render Dashboard → Service → Manual Deploy → Deploy latest commit
```

### Cleaner

```bash
# Пересоберите EXE
cd cleaner
.\СОБРАТЬ_EXE.bat

# Создайте новый GitHub Release
git tag -a v1.5.1 -m "Update"
git push origin v1.5.1

# Загрузите новый EXE
```

## 📊 Мониторинг

### Render Dashboard

- **Logs:** Просмотр логов в реальном времени
- **Metrics:** CPU, Memory, Network usage
- **Events:** История деплоев

### Alerts

Настройте уведомления:
1. Service → Settings → Notifications
2. Email или Slack webhook
3. Уведомления о падениях, деплоях

## 💰 Стоимость

### Free Plan (текущий)

- **Website:** Free (750 часов/месяц)
- **Discord Bot:** Free (750 часов/месяц)
- **Database:** Free (90 дней, потом $7/месяц)

**Ограничения Free Plan:**
- Засыпает после 15 минут неактивности
- Холодный старт ~30 секунд
- 512 MB RAM
- Shared CPU

### Paid Plans

**Starter ($7/месяц на сервис):**
- Не засыпает
- 512 MB RAM
- Shared CPU
- Автоматические деплои

**Standard ($25/месяц на сервис):**
- 2 GB RAM
- Dedicated CPU
- Приоритетная поддержка

## 🔐 Безопасность

### Секреты

- ✅ Используйте Environment Variables
- ✅ Никогда не коммитьте .env файлы
- ✅ Используйте сильные SECRET_KEY
- ✅ Регулярно меняйте токены

### Database

- ✅ Используйте Internal URL
- ✅ Регулярные бэкапы
- ✅ Ограничьте доступ

### HTTPS

Render автоматически предоставляет HTTPS сертификаты.

## 📝 Чеклист деплоя

- [ ] GitHub репозиторий создан и запушен
- [ ] Discord приложение настроено
- [ ] PostgreSQL база создана
- [ ] Website задеплоен и работает
- [ ] Discord Bot задеплоен и онлайн
- [ ] OAuth работает
- [ ] Database подключена
- [ ] Cleaner EXE собран
- [ ] Все секреты в безопасности
- [ ] Документация обновлена

---

**Готово!** Все компоненты TTFD задеплоены и работают! 🚀
