# Система верификации

## Описание
Автоматическая система верификации новых участников сервера через реакции.

## Как работает
1. При запуске бота создаётся сообщение с embed в канале верификации
2. Пользователь нажимает на реакцию ✅
3. Бот автоматически выдаёт роль верифицированного участника
4. Если пользователь убирает реакцию - роль снимается

## Настройка

### ID каналов и ролей
В файле `py/verification_system.py`:
```python
VERIFICATION_CHANNEL_ID = 997173753924554832  # ID канала верификации
VERIFIED_ROLE_ID = 997163765806153728          # ID роли для выдачи
```

### Изображение
Система использует изображение из `фотографии/image.png`
Если файл не найден - сообщение отправляется без картинки

## Команды

### !setupverification (только для администраторов)
Настроить систему верификации вручную
- Создаёт новое сообщение верификации
- Сохраняет ID сообщения в `json/verification_message.json`

## Файлы системы

### py/verification_system.py
Основной файл системы верификации:
- `setup_verification()` - настройка системы при запуске
- `handle_verification_reaction()` - обработка добавления реакции
- `handle_verification_reaction_remove()` - обработка удаления реакции

### json/verification_message.json
Хранит ID сообщения верификации:
```json
{
    "message_id": 123456789,
    "channel_id": 997173753924554832
}
```

## Интеграция в bot.py

### Импорт
```python
import verification_system
```

### При запуске (on_ready)
```python
await verification_system.setup_verification(bot)
```

### Обработчики событий
```python
@bot.event
async def on_raw_reaction_add(payload):
    await verification_system.handle_verification_reaction(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    await verification_system.handle_verification_reaction_remove(bot, payload)
```

## Особенности
- Система автоматически проверяет существование старого сообщения
- Если сообщение не найдено - создаётся новое
- Бот игнорирует свои собственные реакции
- Отправляет личное сообщение пользователю после верификации (опционально)
- Использует стилизованный шрифт через `font_converter`

## Логи
Система выводит подробные логи:
- `[+]` - успешные операции
- `[!]` - ошибки и предупреждения
- `[*]` - информационные сообщения
