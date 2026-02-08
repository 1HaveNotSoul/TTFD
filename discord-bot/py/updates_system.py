# Упрощённая система уведомлений об обновлениях

import discord
from datetime import datetime, timezone, timedelta
import json
import os
from py.update_version import bump_version, get_current_version

# ID канала для уведомлений
UPDATES_CHANNEL_ID = 1466923990936326294

# Путь к файлу автообновления
AUTO_UPDATE_FILE = "json/auto_update.json"

# Часовой пояс МСК (UTC+3)
MSK = timezone(timedelta(hours=3))


def load_auto_update():
    """Загрузить настройки автообновления"""
    if os.path.exists(AUTO_UPDATE_FILE):
        with open(AUTO_UPDATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"enabled": False, "changes": []}



def save_auto_update(auto_update_info):
    """Сохранить настройки автообновления"""
    os.makedirs('json', exist_ok=True)
    with open(AUTO_UPDATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(auto_update_info, f, ensure_ascii=False, indent=2)


def set_auto_update(changes):
    """Установить автообновление при следующем запуске"""
    auto_update_info = {
        "enabled": True,
        "changes": changes if isinstance(changes, list) else [changes]
    }
    save_auto_update(auto_update_info)
    print(f"✅ Автообновление установлено: {changes}")


def clear_auto_update():
    """Очистить автообновление"""
    auto_update_info = {
        "enabled": False,
        "changes": []
    }
    save_auto_update(auto_update_info)


async def send_update_notification(bot, changes):
    """
    Отправить уведомление об обновлении
    
    Формат:
    Обновление: 1.4
    08.02.2026 12:30 МСК
    
    Список изменений:
    · изменение 1
    · изменение 2
    """
    try:
        channel = bot.get_channel(UPDATES_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Канал обновлений не найден (ID: {UPDATES_CHANNEL_ID})")
            return False
        
        # Увеличиваем версию (автоматически сохраняется в файл)
        version = bump_version()
        
        # Текущая дата и время (МСК)
        now = datetime.now(MSK)
        date_str = now.strftime("%d.%m.%Y %H:%M")
        
        # Формируем список изменений
        if isinstance(changes, str):
            changes = [changes]
        
        changes_text = "\n".join([f"· {change}" for change in changes])
        
        # Формируем сообщение
        message_text = f"""**Обновление: {version}**
{date_str} МСК

**Список изменений:**
{changes_text}"""
        
        # Отправляем сообщение
        await channel.send(message_text)
        
        print(f"✅ Уведомление об обновлении {version} отправлено в #{channel.name}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        import traceback
        traceback.print_exc()
        return False


async def check_auto_update(bot):
    """Проверить и выполнить автообновление при запуске"""
    auto_update_info = load_auto_update()
    
    if auto_update_info.get('enabled') and auto_update_info.get('changes'):
        print("🔄 Обнаружено автообновление, отправка уведомления...")
        
        # Получаем все накопленные изменения
        all_changes = auto_update_info['changes']
        
        # Отправляем обновление
        success = await send_update_notification(bot, all_changes)
        
        if success:
            print(f"✅ Уведомление об обновлении отправлено")
            # Очищаем автообновление после успешной отправки
            clear_auto_update()
        else:
            print("❌ Ошибка выполнения автообновления")
        
        return success
    
    return False
