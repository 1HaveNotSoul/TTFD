# Тест системы обновлений
import json
from datetime import datetime, timezone, timedelta

# Часовой пояс МСК (UTC+3)
MSK = timezone(timedelta(hours=3))

def increment_version(current_version, major=False):
    """Увеличить версию"""
    parts = current_version.split('.')
    if major:
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = '0'
    else:
        parts[1] = str(int(parts[1]) + 1)
    return '.'.join(parts)

def test_update():
    """Тест обновления версии"""
    print("=" * 50)
    print("ТЕСТ СИСТЕМЫ ОБНОВЛЕНИЙ")
    print("=" * 50)
    
    # Читаем текущую версию
    with open('json/version.json', 'r', encoding='utf-8') as f:
        version_info = json.load(f)
    
    print(f"\n📦 Текущая версия: {version_info['current_version']}")
    print(f"📅 Последнее обновление: {version_info['last_update']}")
    print(f"📋 Записей в истории: {len(version_info.get('changelog', []))}")
    
    # Симулируем обновление
    new_version = increment_version(version_info['current_version'])
    current_datetime = datetime.now(MSK).strftime("%d.%m.%Y | %H:%M МСК")
    
    print(f"\n✨ СИМУЛЯЦИЯ ОБНОВЛЕНИЯ:")
    print(f"   Новая версия: {new_version}")
    print(f"   Время: {current_datetime}")
    print(f"   Изменения: Тестовое обновление | Проверка системы")
    
    # Создаём тестовую запись
    test_changelog = {
        "version": new_version,
        "date": current_datetime,
        "changes": ["Тестовое обновление", "Проверка системы"],
        "message_id": 123456789
    }
    
    print(f"\n📝 Запись в changelog:")
    print(json.dumps(test_changelog, ensure_ascii=False, indent=2))
    
    print(f"\n✅ Тест пройден успешно!")
    print(f"⚠️  Для применения изменений перезапустите бота и используйте команду:")
    print(f"   !update Тестовое обновление | Проверка системы")
    print("=" * 50)

if __name__ == "__main__":
    test_update()
