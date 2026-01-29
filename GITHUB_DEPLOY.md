# 📦 Деплой на GitHub

## Шаг 1: Инициализация Git

```bash
cd TTFD-Website
git init
git add .
git commit -m "Initial commit: TTFD Discord Bot with Website"
```

## Шаг 2: Подключение к GitHub

```bash
git remote add origin https://github.com/1HaveNotSoul/TTFD.git
git branch -M main
git push -u origin main
```

## Шаг 3: Обновление кода

После изменений:

```bash
git add .
git commit -m "Описание изменений"
git push
```

## 📝 Важно!

### Файлы НЕ для GitHub (уже в .gitignore):
- `.env` - Содержит токены и секреты
- `*.json` - Данные пользователей
- `__pycache__/` - Кеш Python

### Что загружается:
- ✅ Исходный код (*.py)
- ✅ HTML шаблоны
- ✅ Документация (*.md)
- ✅ requirements.txt
- ✅ .env.example (пример настроек)

## 🌐 Хостинг для сайта

### Вариант 1: Heroku

1. Создай `Procfile`:
```
web: python main.py
```

2. Создай `runtime.txt`:
```
python-3.11.0
```

3. Деплой:
```bash
heroku create ttfd-bot
git push heroku main
```

### Вариант 2: Railway.app

1. Подключи GitHub репозиторий
2. Настрой переменные окружения (DISCORD_TOKEN, GUILD_ID)
3. Автоматический деплой при push

### Вариант 3: Render.com

1. Подключи GitHub
2. Выбери "Web Service"
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python main.py`

### Вариант 4: VPS (Рекомендуется)

```bash
# На сервере
git clone https://github.com/1HaveNotSoul/TTFD.git
cd TTFD
pip install -r requirements.txt

# Создай .env файл
nano .env
# Заполни DISCORD_TOKEN, GUILD_ID и т.д.

# Запусти с screen
screen -S ttfd
python main.py
# Ctrl+A, D для отключения
```

## 🔒 Безопасность

**НИКОГДА не загружай на GitHub:**
- Discord токены
- Пароли
- API ключи
- Данные пользователей

Используй `.env` файл и добавь его в `.gitignore`!

## 📊 Структура репозитория

```
TTFD/
├── .gitignore          # Игнорируемые файлы
├── README.md           # Главная документация
├── GITHUB_DEPLOY.md    # Эта инструкция
├── bot.py              # Discord бот
├── web.py              # Веб-сервер
├── main.py             # Запуск
├── config.py           # Конфигурация
├── database.py         # База данных
├── requirements.txt    # Зависимости
├── .env.example        # Пример настроек
└── templates/          # HTML страницы
    ├── index.html
    ├── game.html
    ├── leaderboard.html
    ├── ranks.html
    ├── register.html
    ├── login.html
    ├── profile.html
    └── settings.html
```

## 🚀 Готово!

Теперь твой код на GitHub: https://github.com/1HaveNotSoul/TTFD

Поделись ссылкой с друзьями! 🎉
