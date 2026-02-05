# Система уведомлений об обновлениях

import discord
from datetime import datetime, timezone, timedelta
import json
import os
from font_converter import convert_to_font
from theme import BotTheme

# ID канала для уведомлений
UPDATES_CHANNEL_ID = 1466923990936326294

# Путь к файлу версии
VERSION_FILE = "json/version.json"

# Путь к файлу автообновления
AUTO_UPDATE_FILE = "json/auto_update.json"

# Путь к файлу ID сообщения со списком обновлений
UPDATES_LIST_MESSAGE_FILE = "json/updates_list_message.json"

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
    with open(AUTO_UPDATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(auto_update_info, f, ensure_ascii=False, indent=2)

def set_auto_update(changes):
    """Установить автообновление при следующем запуске"""
    auto_update_info = {
        "enabled": True,
        "changes": changes
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

def load_updates_list_message_id():
    """Загрузить ID сообщения со списком обновлений"""
    try:
        if os.path.exists(UPDATES_LIST_MESSAGE_FILE):
            with open(UPDATES_LIST_MESSAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('message_id')
    except Exception as e:
        print(f"[!] Ошибка загрузки ID сообщения списка обновлений: {e}")
    return None

def save_updates_list_message_id(message_id):
    """Сохранить ID сообщения со списком обновлений"""
    try:
        os.makedirs('json', exist_ok=True)
        data = {
            'message_id': message_id,
            'channel_id': UPDATES_CHANNEL_ID
        }
        with open(UPDATES_LIST_MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[+] Сохранён ID сообщения списка обновлений: {message_id}")
    except Exception as e:
        print(f"[!] Ошибка сохранения ID сообщения: {e}")

def load_version_info():
    """Загрузить информацию о версии"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "current_version": "1.0",
        "last_update": datetime.now(MSK).strftime("%d.%m.%Y | %H:%M МСК"),
        "changelog": []
    }

def save_version_info(version_info):
    """Сохранить информацию о версии"""
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)

def increment_version(current_version, major=False):
    """
    Увеличить версию
    major=True: 1.0 -> 2.0
    major=False: 1.0 -> 1.1
    """
    parts = current_version.split('.')
    if major:
        parts[0] = str(int(parts[0]) + 1)
        parts[1] = '0'
    else:
        parts[1] = str(int(parts[1]) + 1)
    return '.'.join(parts)

async def send_update_notification(bot, changes, major=False, custom_version=None):
    """
    Отправить уведомление об обновлении с автоматической версией
    Бот автоматически отправляет всю информацию в канал обновлений
    
    Args:
        bot: Экземпляр бота
        changes: Список изменений (список строк)
        major: True для крупного обновления (1.0 -> 2.0), False для минорного (1.0 -> 1.1)
        custom_version: Пользовательская версия (опционально)
    """
    try:
        channel = bot.get_channel(UPDATES_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Канал обновлений не найден (ID: {UPDATES_CHANNEL_ID})")
            return False
        
        # Загружаем текущую версию
        version_info = load_version_info()
        
        # Определяем новую версию
        if custom_version:
            new_version = custom_version
        else:
            new_version = increment_version(version_info['current_version'], major)
        
        # Текущая дата и время (МСК)
        current_datetime = datetime.now(MSK).strftime("%d.%m.%Y | %H:%M МСК")
        
        # Создаём embed с обновлением
        embed = BotTheme.create_embed(
            title=convert_to_font(f"🎉 обновление {new_version}"),
            description=convert_to_font("новые функции и улучшения!"),
            embed_type='info'
        )
        embed.timestamp = datetime.now()
        
        # Добавляем версию
        embed.add_field(
            name=convert_to_font("📦 Текущая версия"),
            value=convert_to_font(new_version),
            inline=True
        )
        
        # Добавляем дату и время (МСК не конвертируем в шрифт)
        embed.add_field(
            name=convert_to_font("📅 Последнее обновление"),
            value=current_datetime,  # Без convert_to_font для правильного отображения МСК
            inline=True
        )
        
        # Добавляем список изменений
        if changes:
            changes_text = "\n".join([f"• {convert_to_font(change)}" for change in changes])
            embed.add_field(
                name=convert_to_font("✨ список изменений"),
                value=changes_text,
                inline=False
            )
        
        # Добавляем footer
        embed.set_footer(
            text=convert_to_font("TTFD Bot Updates"),
            icon_url=bot.user.display_avatar.url if bot.user else None
        )
        
        # Отправляем сообщение с обновлением
        message = await channel.send(embed=embed)
        
        # Сохраняем информацию о версии
        version_info['current_version'] = new_version
        version_info['last_update'] = current_datetime
        version_info['changelog'].append({
            "version": new_version,
            "date": current_datetime,
            "changes": changes,
            "message_id": message.id
        })
        save_version_info(version_info)
        
        print(f"✅ Уведомление об обновлении {new_version} отправлено в #{channel.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        import traceback
        traceback.print_exc()
        return False

async def send_startup_notification(bot):
    """Отправить уведомление о запуске бота"""
    try:
        channel = bot.get_channel(UPDATES_CHANNEL_ID)
        if not channel:
            return False
        
        version_info = load_version_info()
        
        embed = BotTheme.create_embed(
            title=convert_to_font("🟢 бот запущен"),
            description=convert_to_font("бот успешно запущен и готов к работе!"),
            embed_type='success'
        )
        embed.timestamp = datetime.now()
        
        embed.add_field(
            name=convert_to_font("📦 Версия"),
            value=convert_to_font(version_info['current_version']),
            inline=True
        )
        embed.add_field(
            name=convert_to_font("🌐 Серверов"),
            value=convert_to_font(str(len(bot.guilds))),
            inline=True
        )
        embed.add_field(
            name=convert_to_font("👥 Пользователей"),
            value=convert_to_font(str(len(bot.users))),
            inline=True
        )
        
        await channel.send(embed=embed)
        print(f"✅ Уведомление о запуске отправлено в #{channel.name}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления о запуске: {e}")
        return False

async def create_updates_list(bot):
    """Создать или обновить список обновлений в канале"""
    try:
        channel = bot.get_channel(UPDATES_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Канал обновлений не найден (ID: {UPDATES_CHANNEL_ID})")
            return False
        
        version_info = load_version_info()
        changelog = version_info.get('changelog', [])
        
        # Создаём embed со списком всех обновлений
        embed = BotTheme.create_embed(
            title=convert_to_font("📋 история обновлений"),
            description=convert_to_font("все обновления бота"),
            embed_type='info'
        )
        embed.timestamp = datetime.now()
        
        embed.add_field(
            name=convert_to_font("📦 Текущая версия"),
            value=convert_to_font(version_info['current_version']),
            inline=True
        )
        
        embed.add_field(
            name=convert_to_font("📅 Последнее обновление"),
            value=version_info['last_update'],  # Без convert_to_font
            inline=True
        )
        
        # Если есть история обновлений
        if changelog:
            # Показываем последние 5 обновлений
            recent_updates = changelog[-5:] if len(changelog) > 5 else changelog
            
            for update in reversed(recent_updates):
                changes_text = "\n".join([f"• {convert_to_font(change)}" for change in update['changes']])
                # Дата без конвертации в шрифт для правильного отображения МСК
                date_str = update['date']
                if 'МСК' not in date_str and 'MSK' not in date_str.upper():
                    date_str = f"{date_str} МСК"
                embed.add_field(
                    name=convert_to_font(f"Версия {update['version']}") + f" ({date_str})",
                    value=changes_text,
                    inline=False
                )
        else:
            embed.add_field(
                name=convert_to_font("ℹ️ Информация"),
                value=convert_to_font("История обновлений пока пуста. Используйте команду !update для добавления обновлений."),
                inline=False
            )
        
        embed.set_footer(
            text=convert_to_font("TTFD Bot Updates"),
            icon_url=bot.user.display_avatar.url if bot.user else None
        )
        
        # Проверяем, есть ли уже сообщение
        existing_message_id = load_updates_list_message_id()
        if existing_message_id:
            try:
                message = await channel.fetch_message(existing_message_id)
                await message.edit(embed=embed)
                print(f"✅ Список обновлений обновлён (Message ID: {existing_message_id})")
                return True
            except discord.NotFound:
                print("[!] Старое сообщение не найдено, создаю новое")
        
        # Отправляем новое сообщение
        message = await channel.send(embed=embed)
        save_updates_list_message_id(message.id)
        print(f"✅ Список обновлений создан в #{channel.name} (Message ID: {message.id})")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания списка обновлений: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_current_version():
    """Получить текущую версию"""
    version_info = load_version_info()
    return version_info['current_version']

def get_changelog():
    """Получить историю изменений"""
    version_info = load_version_info()
    return version_info.get('changelog', [])

async def check_auto_update(bot):
    """Проверить и выполнить автообновление при запуске"""
    auto_update_info = load_auto_update()
    
    if auto_update_info.get('enabled') and auto_update_info.get('changes'):
        print("🔄 Обнаружено автообновление, отправка уведомления...")
        
        # Отправляем обновление
        success = await send_update_notification(
            bot=bot,
            changes=auto_update_info['changes'],
            major=False
        )
        
        if success:
            print("✅ Автообновление выполнено успешно")
            # Очищаем автообновление
            clear_auto_update()
        else:
            print("❌ Ошибка выполнения автообновления")
        
        return success
    
    return False

