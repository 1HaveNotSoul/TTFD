# Система верификации

import discord
from discord.ext import commands
import json
import os
import asyncio
from font_converter import convert_to_font
from theme import BotTheme, success_embed

# ID канала верификации
VERIFICATION_CHANNEL_ID = 997173753924554832

# ID роли для выдачи
VERIFIED_ROLE_ID = 997163765806153728

# Файл для хранения ID сообщения верификации
VERIFICATION_MESSAGE_FILE = 'json/verification_message.json'

def load_verification_message_id():
    """Загрузить ID сообщения верификации"""
    try:
        if os.path.exists(VERIFICATION_MESSAGE_FILE):
            with open(VERIFICATION_MESSAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('message_id')
    except Exception as e:
        print(f"[!] Ошибка загрузки ID сообщения верификации: {e}")
    return None

def save_verification_message_id(message_id):
    """Сохранить ID сообщения верификации"""
    try:
        os.makedirs('json', exist_ok=True)
        data = {
            'message_id': message_id,
            'channel_id': VERIFICATION_CHANNEL_ID
        }
        with open(VERIFICATION_MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[+] Сохранён ID сообщения верификации: {message_id}")
    except Exception as e:
        print(f"[!] Ошибка сохранения ID сообщения: {e}")

async def setup_verification(bot):
    """Настроить систему верификации"""
    try:
        channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
        if not channel:
            print(f"[!] Канал верификации не найден (ID: {VERIFICATION_CHANNEL_ID})")
            return False
        
        print(f"[+] Канал верификации найден: {channel.name}")
        
        # Проверяем, есть ли уже сообщение
        existing_message_id = load_verification_message_id()
        if existing_message_id:
            try:
                message = await channel.fetch_message(existing_message_id)
                print(f"✅ Сообщение верификации уже существует (ID: {existing_message_id})")
                print(f"   Не создаю новое сообщение - использую существующее")
                
                # Проверяем, есть ли реакция ✅
                has_checkmark = False
                for reaction in message.reactions:
                    if str(reaction.emoji) == '✅':
                        has_checkmark = True
                        break
                
                # Если реакции нет - добавляем
                if not has_checkmark:
                    await message.add_reaction('✅')
                    print(f"✅ Добавлена реакция ✅ к существующему сообщению")
                
                # Удаляем все ДРУГИЕ сообщения бота в канале (кроме текущего)
                try:
                    deleted_count = 0
                    async for msg in channel.history(limit=100):
                        if msg.author == bot.user and msg.id != existing_message_id:
                            await msg.delete()
                            deleted_count += 1
                            await asyncio.sleep(0.5)
                    if deleted_count > 0:
                        print(f"🗑️ Удалено {deleted_count} старых сообщений верификации")
                except Exception as e:
                    print(f"⚠️ Ошибка очистки старых сообщений: {e}")
                
                return True
            except discord.NotFound:
                print("⚠️ Старое сообщение не найдено, создаю новое")
                # НЕ удаляем все сообщения, только создаём новое
            except Exception as e:
                print(f"⚠️ Ошибка проверки существующего сообщения: {e}")
        
        # Удаляем ВСЕ старые сообщения бота перед созданием нового
        try:
            deleted_count = 0
            async for msg in channel.history(limit=100):
                if msg.author == bot.user:
                    await msg.delete()
                    deleted_count += 1
                    await asyncio.sleep(0.5)
            if deleted_count > 0:
                print(f"🗑️ Удалено {deleted_count} старых сообщений перед созданием нового")
        except Exception as e:
            print(f"⚠️ Ошибка очистки канала: {e}")
        
        # Создаём embed
        embed = success_embed(
            title=convert_to_font("✅ верификация"),
            description=convert_to_font("нажми на реакцию ниже, чтобы получить доступ к серверу")
        )
        
        embed.set_footer(text=convert_to_font("нажми ✅ для верификации"))
        
        # Путь к картинке
        image_path = 'фотографии/image.png'
        
        # Проверяем существование файла
        if not os.path.exists(image_path):
            print(f"[!] Файл не найден: {image_path}")
            # Отправляем без картинки
            message = await channel.send(embed=embed)
        else:
            # Отправляем с картинкой
            file = discord.File(image_path, filename='verification.png')
            embed.set_image(url='attachment://verification.png')
            message = await channel.send(file=file, embed=embed)
        
        # Добавляем реакцию
        await message.add_reaction('✅')
        
        # Сохраняем ID сообщения
        save_verification_message_id(message.id)
        
        print(f"[+] Сообщение верификации создано (ID: {message.id})")
        return True
        
    except Exception as e:
        print(f"[!] Ошибка настройки верификации: {e}")
        import traceback
        traceback.print_exc()
        return False

async def handle_verification_reaction(bot, payload):
    """Обработать реакцию на сообщение верификации"""
    try:
        # Проверяем, что это нужный канал
        if payload.channel_id != VERIFICATION_CHANNEL_ID:
            return
        
        # Проверяем, что это нужное сообщение
        verification_message_id = load_verification_message_id()
        if not verification_message_id or payload.message_id != verification_message_id:
            return
        
        # Проверяем, что это нужная реакция
        if str(payload.emoji) != '✅':
            return
        
        # Проверяем, что это не бот
        if payload.user_id == bot.user.id:
            return
        
        # Получаем сервер и участника
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        # Получаем роль
        role = guild.get_role(VERIFIED_ROLE_ID)
        if not role:
            print(f"[!] Роль верификации не найдена (ID: {VERIFIED_ROLE_ID})")
            return
        
        # Проверяем, есть ли уже роль
        if role in member.roles:
            print(f"[*] У {member.name} уже есть роль верификации")
            return
        
        # Выдаём роль
        await member.add_roles(role, reason="Верификация через реакцию")
        print(f"[+] Роль верификации выдана: {member.name}")
        
        # Отправляем личное сообщение (опционально)
        try:
            dm_embed = success_embed(
                title=convert_to_font("✅ верификация пройдена"),
                description=convert_to_font("добро пожаловать на сервер!")
            )
            await member.send(embed=dm_embed)
        except:
            # Если не удалось отправить ЛС - не критично
            pass
        
    except Exception as e:
        print(f"[!] Ошибка обработки реакции верификации: {e}")
        import traceback
        traceback.print_exc()

async def handle_verification_reaction_remove(bot, payload):
    """Обработать удаление реакции (снять роль)"""
    try:
        # Проверяем, что это нужный канал
        if payload.channel_id != VERIFICATION_CHANNEL_ID:
            return
        
        # Проверяем, что это нужное сообщение
        verification_message_id = load_verification_message_id()
        if not verification_message_id or payload.message_id != verification_message_id:
            return
        
        # Проверяем, что это нужная реакция
        if str(payload.emoji) != '✅':
            return
        
        # Проверяем, что это не бот
        if payload.user_id == bot.user.id:
            return
        
        # Получаем сервер и участника
        guild = bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        # Получаем роль
        role = guild.get_role(VERIFIED_ROLE_ID)
        if not role:
            return
        
        # Проверяем, есть ли роль
        if role not in member.roles:
            return
        
        # Снимаем роль
        await member.remove_roles(role, reason="Снята реакция верификации")
        print(f"[-] Роль верификации снята: {member.name}")
        
    except Exception as e:
        print(f"[!] Ошибка снятия роли верификации: {e}")
