#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Update Handler - автоматическое добавление обновлений из коммитов
"""

import json
import os
import subprocess
import sys

# Путь к файлу автообновления
AUTO_UPDATE_FILE = 'json/auto_update.json'


def load_auto_update():
    """Загрузить текущий файл автообновления"""
    if os.path.exists(AUTO_UPDATE_FILE):
        with open(AUTO_UPDATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "enabled": False,
        "changes": []
    }


def save_auto_update(data):
    """Сохранить файл автообновления"""
    os.makedirs('json', exist_ok=True)
    with open(AUTO_UPDATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_last_commit_message():
    """Получить сообщение последнего коммита"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Ошибка получения сообщения коммита: {e}")
        return None


def format_change_message(message):
    """Форматировать сообщение изменения"""
    # Убираем лишние пробелы
    message = ' '.join(message.split())
    
    # Делаем первую букву строчной (для единообразия)
    if message and message[0].isupper():
        message = message[0].lower() + message[1:]
    
    return message


def add_update(commit_message):
    """Добавить обновление из коммита"""
    if not commit_message:
        print(f"⚠️ Пустое сообщение коммита")
        return False
    
    # Форматируем сообщение
    formatted_message = format_change_message(commit_message)
    
    # Загружаем текущие обновления
    auto_update = load_auto_update()
    
    # Проверяем дубликаты
    if formatted_message in auto_update.get('changes', []):
        print(f"ℹ️ Изменение уже добавлено: {formatted_message}")
        return False
    
    # Добавляем изменение
    if 'changes' not in auto_update:
        auto_update['changes'] = []
    
    auto_update['changes'].append(formatted_message)
    auto_update['enabled'] = True
    
    # Сохраняем
    save_auto_update(auto_update)
    
    print(f"✅ Добавлено обновление: {formatted_message}")
    print(f"📊 Всего изменений: {len(auto_update['changes'])}")
    
    return True


def main():
    """Главная функция"""
    print("=" * 60)
    print("🔄 Git Update Handler")
    print("=" * 60)
    
    # Получаем сообщение последнего коммита
    commit_message = get_last_commit_message()
    
    if not commit_message:
        print("❌ Не удалось получить сообщение коммита")
        return 1
    
    print(f"📝 Сообщение коммита: {commit_message}")
    
    # Добавляем обновление
    success = add_update(commit_message)
    
    if success:
        print("\n✅ Обновление добавлено!")
        print("💡 При следующем запуске бота оно будет отправлено в Discord")
    else:
        print("\nℹ️ Обновление не добавлено")
    
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
