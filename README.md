# 🎮 TTFD - The First Descendants Project

Единый проект, объединяющий все компоненты экосистемы TTFD.

## 📦 Компоненты проекта

### 🌐 TTFD-Website
Веб-сайт с профилями, кастомизацией и Discord OAuth авторизацией.

**Технологии:** Flask, Discord OAuth, PostgreSQL  
**Деплой:** Render.com  
**Порт:** 10000

### 🤖 TTFD-Discord
Discord бот с системой рангов, магазином, тикетами и верификацией.

**Технологии:** discord.py, PostgreSQL  
**Деплой:** Render.com (Background Worker)

### 🧹 TTFD-Cleaner
Инструмент для очистки и оптимизации Windows 10/11.

**Технологии:** Python (tkinter), C# (.NET 8)  
**Распространение:** Standalone EXE

## 🚀 Быстрый старт

### Клонирование репозитория

```bash
git clone https://github.com/yourusername/TTFD.git
cd TTFD
```

### Установка зависимостей

```bash
# Website
cd website
pip install -r requirements.txt

# Discord Bot
cd ../discord-bot
pip install -r requirements.txt

# Cleaner (только для разработки)
cd ../cleaner
pip install -r requirements.txt
```

### Настройка переменных окружения

Создайте `.env` файлы в каждом проекте на основе `.env.example`:

```bash
# Website
cp website/.env.example website/.env

# Discord Bot
cp discord-bot/.env.example discord-bot/.env
```

Заполните необходимые данные в `.env` файлах.

### Запуск проектов

```bash
# Website
cd website
python main.py

# Discord Bot
cd discord-bot
python main.py

# Cleaner
cd cleaner
python main_menu.py
```

## 📁 Структура проекта

```
TTFD/
├── website/              # Веб-сайт (Flask)
│   ├── static/
│   ├── templates/
│   ├── app.py
│   ├── main.py
│   ├── config.py
│   ├── discord_oauth.py
│   ├── database.py
│   ├── requirements.txt
│   └── .env.example
│
├── discord-bot/          # Discord бот
│   ├── py/
│   │   ├── bot.py
│   │   ├── commands_manager.py
│   │   ├── verification_system.py
│   │   └── tickets_system.py
│   ├── md/
│   ├── json/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── cleaner/              # Windows Cleaner
│   ├── Backend/          # C# Backend
│   ├── sections/         # GUI разделы
│   ├── assets/           # Ассеты меню
│   ├── main_menu.py
│   ├── gui.py
│   ├── requirements.txt
│   └── README.md
│
├── docs/                 # Общая документация
│   ├── DEPLOYMENT.md
│   ├── ARCHITECTURE.md
│   └── CONTRIBUTING.md
│
├── .gitignore
├── README.md
└── LICENSE
```

## 🔧 Конфигурация

### Website (.env)

```env
SECRET_KEY=your_secret_key
PORT=10000
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=https://your-domain.com/auth/discord/callback
DATABASE_URL=postgresql://user:password@host/database
```

### Discord Bot (.env)

```env
DISCORD_TOKEN=your_bot_token
GUILD_ID=your_guild_id
```

## 🚀 Деплой

### Railway.app (Рекомендуется) ⭐

**Преимущества:**
- ✅ $5 бесплатных кредитов каждый месяц
- ✅ Не засыпает (в отличие от Render Free)
- ✅ PostgreSQL включён
- ✅ Простой деплой из GitHub
- ✅ Автоматические деплои

**Быстрый старт:**
1. Зарегистрируйтесь на https://railway.app
2. Создайте проект из GitHub репозитория
3. Добавьте PostgreSQL базу
4. Деплойте Website (Root Directory: `website`)
5. Деплойте Discord Bot (Root Directory: `discord-bot`)

**Подробная инструкция:** [ДЕПЛОЙ_RAILWAY.md](ДЕПЛОЙ_RAILWAY.md)  
**Быстрая шпаргалка:** [RAILWAY_БЫСТРЫЙ_СТАРТ.txt](RAILWAY_БЫСТРЫЙ_СТАРТ.txt)

---

### Render.com (Альтернатива)

1. **Website (Web Service)**
   - Build Command: `cd website && pip install -r requirements.txt`
   - Start Command: `cd website && python main.py`
   - Environment Variables: добавьте все из `.env`

2. **Discord Bot (Background Worker)**
   - Build Command: `cd discord-bot && pip install -r requirements.txt`
   - Start Command: `cd discord-bot && python main.py`
   - Environment Variables: добавьте все из `.env`

3. **PostgreSQL Database**
   - Создайте PostgreSQL инстанс на Render
   - Скопируйте Internal Database URL
   - Добавьте в Environment Variables обоих сервисов

**Подробная инструкция:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Cleaner (Standalone)

Cleaner распространяется как standalone EXE:

```bash
cd cleaner
.\СОБРАТЬ_EXE.bat
```

Готовый файл: `cleaner/dist/TTFD-Cleaner-Menu.exe`

## 📖 Документация

- **Website:** [website/README.md](website/README.md)
- **Discord Bot:** [discord-bot/README_КОМАНДЫ.md](discord-bot/README_КОМАНДЫ.md)
- **Cleaner:** [cleaner/README.md](cleaner/README.md)
- **Deployment:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Architecture:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 🛠️ Разработка

### Требования

- Python 3.11+
- PostgreSQL (для Website и Discord Bot)
- .NET 8 SDK (для Cleaner Backend)
- Git

### Ветки

- `main` - стабильная версия
- `dev` - разработка
- `feature/*` - новые функции
- `hotfix/*` - срочные исправления

### Коммиты

Используйте Conventional Commits:

```
feat: добавлена новая команда !dice
fix: исправлена ошибка в системе рангов
docs: обновлена документация
style: форматирование кода
refactor: рефакторинг системы тикетов
test: добавлены тесты
chore: обновлены зависимости
```

## 🤝 Вклад

1. Fork репозитория
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'feat: add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 👥 Команда

TTFD Team

## 📞 Поддержка

- Discord: [Ссылка на сервер]
- Website: [Ссылка на сайт]
- Issues: [GitHub Issues](https://github.com/yourusername/TTFD/issues)

## 🎯 Roadmap

### v2.0 (Q1 2026)
- [ ] Интеграция Website ↔ Discord Bot
- [ ] Синхронизация профилей
- [ ] API для Cleaner статистики
- [ ] Мобильная версия сайта

### v2.1 (Q2 2026)
- [ ] Система достижений
- [ ] Расширенная аналитика
- [ ] Cleaner: автоматические обновления
- [ ] Discord Bot: голосовые команды

## ⚠️ Важно

- **Не коммитьте `.env` файлы!**
- **Не коммитьте токены и секреты!**
- **Используйте `.env.example` как шаблон**
- **Всегда тестируйте перед деплоем**

## 🔒 Безопасность

Если вы нашли уязвимость безопасности, пожалуйста, НЕ создавайте публичный issue. Свяжитесь с нами напрямую.

---

**Версия:** 2.0.0  
**Дата:** 05.02.2026  
**Статус:** В разработке

Made with ❤️ by TTFD Team
