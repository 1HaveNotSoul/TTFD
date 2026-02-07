# Discord Bot - Основной файл

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import config
import os

# Автоматический выбор базы данных
if os.getenv('DATABASE_URL'):
    print("🔄 Обнаружен DATABASE_URL, используется PostgreSQL")
    from database_postgres import db
    print("✅ Используется PostgreSQL база данных")
else:
    print("🔄 DATABASE_URL не найден, используется JSON")
    from database import db
    print("✅ Используется JSON база данных")

from font_converter import convert_to_font
import tickets_system
import verification_system
from commands_manager import get_commands_text
from theme import BotTheme, game_embed, profile_embed, success_embed, error_embed, warning_embed
import shop_system
import commands_channel
import updates_system
import voice_tracking
import rank_roles
import game_integration

# Настройка intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.presences = True

# Создание бота
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Статистика бота
bot.stats = {
    'start_time': None,
    'commands_used': 0,
    'messages_seen': 0,
}

# ID канала для списка команд
COMMANDS_CHANNEL_ID = 1466295322002067607

# Файл для хранения ID сообщения со списком команд
COMMANDS_MESSAGE_FILE = 'json/commands_message.json'

# ID сообщения со списком команд (будет загружено из файла)
COMMANDS_MESSAGE_ID = None

def load_commands_message_id():
    """Загрузить ID сообщения со списком команд из файла"""
    global COMMANDS_MESSAGE_ID
    try:
        import json
        import os
        if os.path.exists(COMMANDS_MESSAGE_FILE):
            with open(COMMANDS_MESSAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                COMMANDS_MESSAGE_ID = data.get('message_id')
                if COMMANDS_MESSAGE_ID:
                    print(f"📋 Загружен ID сообщения команд: {COMMANDS_MESSAGE_ID}")
    except Exception as e:
        print(f"⚠️ Не удалось загрузить ID сообщения: {e}")

def save_commands_message_id(message_id):
    """Сохранить ID сообщения со списком команд в файл"""
    global COMMANDS_MESSAGE_ID
    try:
        import json
        from datetime import datetime
        COMMANDS_MESSAGE_ID = message_id
        data = {
            'message_id': message_id,
            'channel_id': COMMANDS_CHANNEL_ID,
            'last_updated': datetime.now().isoformat()
        }
        with open(COMMANDS_MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Сохранён ID сообщения команд: {message_id}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить ID сообщения: {e}")

# ID канала для уведомлений об обновлениях
UPDATES_CHANNEL_ID = 1466923990936326294

# ID роли администратора
ADMIN_ROLE_ID = 1466282400219922536


# ==================== Вспомогательные функции ====================

def is_admin(ctx):
    """Проверить является ли пользователь администратором"""
    admin_role = ctx.guild.get_role(ADMIN_ROLE_ID)
    return admin_role in ctx.author.roles if admin_role else False

def create_progress_bar(current, total, length=10):
    """Создать прогресс-бар"""
    filled = int((current / total) * length) if total > 0 else 0
    bar = "█" * filled + "░" * (length - filled)
    percentage = int((current / total) * 100) if total > 0 else 0
    return f"{bar} {percentage}%"

def get_next_rank_info(user):
    """Получить информацию о следующем ранге"""
    current_rank = db.get_rank_info(user['rank_id'])
    all_ranks = db.get_all_ranks()
    
    if user['rank_id'] < len(all_ranks):
        next_rank = all_ranks[user['rank_id']]
        xp_needed = next_rank['required_xp'] - user['xp']
        progress = user['xp'] - current_rank['required_xp']
        total_needed = next_rank['required_xp'] - current_rank['required_xp']
        return {
            'next_rank': next_rank,
            'xp_needed': xp_needed,
            'progress_bar': create_progress_bar(progress, total_needed)
        }
    return None

def get_daily_streak(user):
    """Получить серию ежедневных входов"""
    if 'daily_streak' not in user:
        user['daily_streak'] = 0
        user['last_daily_date'] = None
    return user['daily_streak']

def update_daily_streak(user):
    """Обновить серию ежедневных входов"""
    if 'last_daily_date' not in user or user['last_daily_date'] is None:
        user['daily_streak'] = 1
        user['last_daily_date'] = datetime.now().date().isoformat()
        return 1
    
    last_date = datetime.fromisoformat(user['last_daily_date']).date()
    today = datetime.now().date()
    days_diff = (today - last_date).days
    
    if days_diff == 1:
        # Продолжаем серию
        user['daily_streak'] = user.get('daily_streak', 0) + 1
    elif days_diff > 1:
        # Серия прервана
        user['daily_streak'] = 1
    else:
        # Уже получено сегодня
        return user.get('daily_streak', 1)
    
    user['last_daily_date'] = today.isoformat()
    return user['daily_streak']

# Функция handle_rank_up удалена - роли выдаются автоматически фоновой задачей


# ==================== События бота ====================

@bot.event
async def on_ready():
    """Событие запуска бота"""
    bot.stats['start_time'] = datetime.now()
    
    # Загружаем ID сообщения со списком команд
    load_commands_message_id()
    
    print("=" * 50)
    print(f"✅ Бот успешно запущен!")
    print(f"📛 Имя: {bot.user.name}#{bot.user.discriminator}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🌐 Серверов: {len(bot.guilds)}")
    print(f"👥 Пользователей: {len(bot.users)}")
    print("=" * 50)
    
    # Синхронизация slash команд (если есть)
    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано {len(synced)} slash команд")
    except Exception as e:
        print(f"❌ Ошибка синхронизации команд: {e}")
    
    # Обновление списка команд в канале (ОТКЛЮЧЕНО - дублирует сообщения)
    # print("🔄 Обновление списка команд...")
    # try:
    #     await update_commands_list()
    # except Exception as e:
    #     print(f"❌ Ошибка при обновлении списка команд: {e}")
    #     import traceback
    #     traceback.print_exc()
    
    # Настройка системы верификации
    print("🔄 Настройка системы верификации...")
    try:
        await verification_system.setup_verification(bot)
    except Exception as e:
        print(f"❌ Ошибка настройки верификации: {e}")
        import traceback
        traceback.print_exc()
    
    # Настройка кнопки тикетов
    print("🔄 Настройка кнопки тикетов...")
    try:
        await tickets_system.setup_ticket_button(bot)
    except Exception as e:
        print(f"❌ Ошибка настройки кнопки тикетов: {e}")
        import traceback
        traceback.print_exc()
    
    # Настройка интеграции с игрой
    print("🎮 Настройка интеграции с TTFD Game...")
    try:
        global game_int
        game_int = game_integration.GameIntegration(db)
        game_integration.setup_game_commands(bot, db, game_int)
        print("✅ Интеграция с игрой настроена")
        
        # Синхронизация команд игры с Discord
        print("🔄 Синхронизация команд игры...")
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано {len(synced)} slash команд (включая игровые)")
    except Exception as e:
        print(f"❌ Ошибка настройки интеграции с игрой: {e}")
        import traceback
        traceback.print_exc()
    
    # Проверка автообновления
    print("🔄 Проверка автообновления...")
    try:
        await updates_system.check_auto_update(bot)
    except Exception as e:
        print(f"❌ Ошибка проверки автообновления: {e}")
        import traceback
        traceback.print_exc()
    
    # Запуск фоновых задач
    if not update_bot_status.is_running():
        update_bot_status.start()
        print("✅ Запущена задача обновления статуса")
    
    if not auto_sync_rank_roles.is_running():
        auto_sync_rank_roles.start()
        print("✅ Запущена задача автоматической синхронизации ролей (каждую минуту)")

@bot.event
async def on_message(message):
    """Обработка сообщений"""
    if message.author.bot:
        return
    
    bot.stats['messages_seen'] += 1
    
    # Проверяем, является ли сообщение командой
    if message.content.startswith('!'):
        # Проверяем, в каком канале написана команда
        if commands_channel.is_commands_channel(message.channel.id):
            # В канале команд: обрабатываем и удаляем через 5 минут
            asyncio.create_task(delete_message_after(message, 300))
            await bot.process_commands(message)
        else:
            # В других каналах: отправляем сообщение и удаляем команду
            try:
                # Отправляем сообщение только автору (ephemeral через DM невозможно, используем обычное сообщение)
                warning_msg = await message.channel.send(
                    f"{message.author.mention} " + convert_to_font(f"все команды работают только здесь: <#{commands_channel.COMMANDS_CHANNEL_ID}>")
                )
                # Удаляем команду пользователя сразу
                await message.delete()
                # Удаляем предупреждение через 10 секунд
                asyncio.create_task(delete_message_after(warning_msg, 10))
            except:
                pass
            return
    else:
        # Обычное сообщение (не команда)
        await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    """Событие использования команды"""
    bot.stats['commands_used'] += 1
    
    # Если команда выполнена в канале команд, удаляем ответ бота через 5 минут
    if commands_channel.is_commands_channel(ctx.channel.id):
        # Ждём ответа бота и удаляем его через 5 минут
        async def delete_bot_response():
            await asyncio.sleep(1)  # Ждём пока бот ответит
            async for msg in ctx.channel.history(limit=10):
                if msg.author == bot.user and msg.created_at > ctx.message.created_at:
                    asyncio.create_task(delete_message_after(msg, 300))
                    break
        
        asyncio.create_task(delete_bot_response())

async def delete_message_after(message, delay):
    """Удалить сообщение через указанное время"""
    try:
        await asyncio.sleep(delay)
        await message.delete()
    except:
        pass

@bot.event
async def on_raw_reaction_add(payload):
    """Обработка добавления реакции"""
    await verification_system.handle_verification_reaction(bot, payload)

@bot.event
async def on_raw_reaction_remove(payload):
    """Обработка удаления реакции"""
    await verification_system.handle_verification_reaction_remove(bot, payload)

@bot.event
async def on_voice_state_update(member, before, after):
    """Обработка изменения голосового состояния"""
    await voice_tracking.on_voice_state_update(member, before, after)


# ==================== Фоновые задачи ====================

@tasks.loop(minutes=5)
async def update_bot_status():
    """Обновление статуса бота"""
    statuses = [
        discord.Activity(type=discord.ActivityType.watching, name=f"{len(bot.guilds)} серверов"),
        discord.Activity(type=discord.ActivityType.playing, name="!help для помощи"),
        discord.Activity(type=discord.ActivityType.listening, name="ваши команды"),
    ]
    await bot.change_presence(activity=random.choice(statuses))

@tasks.loop(minutes=1)
async def auto_sync_rank_roles():
    """
    Автоматическая синхронизация ролей каждую минуту
    Проверяет XP всех пользователей и выдаёт роли
    """
    try:
        print("🔄 Автоматическая проверка ролей...")
        
        all_users = db.get_all_users()
        updated_count = 0
        
        for user_id, user_data in all_users.items():
            try:
                xp = user_data.get('xp', 0)
                
                # Находим пользователя на всех серверах
                for guild in bot.guilds:
                    member = guild.get_member(int(user_id))
                    
                    if member:
                        result = await rank_roles.update_user_rank_role(member, xp)
                        
                        if result['success'] and result['action'] == 'added':
                            updated_count += 1
                            print(f"✅ Автоматически выдана роль {result.get('tier')} пользователю {member.name}")
                        
                        break  # Нашли пользователя, выходим из цикла
            
            except Exception as e:
                print(f"⚠️ Ошибка проверки роли для {user_id}: {e}")
        
        if updated_count > 0:
            print(f"✅ Автоматически обновлено ролей: {updated_count}")
    
    except Exception as e:
        print(f"❌ Ошибка автоматической синхронизации ролей: {e}")
        import traceback
        traceback.print_exc()
        discord.Activity(type=discord.ActivityType.playing, name="!help для помощи"),
        discord.Activity(type=discord.ActivityType.listening, name="ваши команды"),
    ]
    await bot.change_presence(activity=random.choice(statuses))


# ==================== Обновление списка команд ====================

def get_all_commands_list():
    """Получить список всех команд бота с описаниями"""
    from commands_manager import get_all_commands
    return get_all_commands()

async def update_commands_list():
    """Обновить список команд в канале"""
    global COMMANDS_MESSAGE_ID
    
    print(f"📝 Начало обновления списка команд (канал ID: {COMMANDS_CHANNEL_ID})...")
    
    try:
        channel = bot.get_channel(COMMANDS_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Канал команд не найден (ID: {COMMANDS_CHANNEL_ID})")
            return
        
        print(f"✅ Канал найден: {channel.name}")
        
        # Получаем отформатированный текст команд
        print("📄 Генерация текста команд...")
        text = get_commands_text()
        print(f"✅ Текст сгенерирован ({len(text)} символов)")
        
        # Если сообщение уже существует - обновляем его
        if COMMANDS_MESSAGE_ID:
            try:
                message = await channel.fetch_message(COMMANDS_MESSAGE_ID)
                await message.edit(content=text)
                print(f"✅ Список команд обновлён (Message ID: {COMMANDS_MESSAGE_ID})")
                return
            except discord.NotFound:
                print("⚠️ Старое сообщение не найдено, создаю новое")
                COMMANDS_MESSAGE_ID = None
            except Exception as e:
                print(f"❌ Ошибка редактирования сообщения: {e}")
        
        # Если сообщения нет - создаём новое
        # Удаляем старые сообщения бота в канале
        try:
            async for message in channel.history(limit=100):
                if message.author == bot.user:
                    await message.delete()
                    await asyncio.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Не удалось очистить старые сообщения: {e}")
        
        # Создаём новое сообщение
        message = await channel.send(text)
        save_commands_message_id(message.id)
        print(f"✅ Список команд создан (Message ID: {message.id})")
        
    except Exception as e:
        print(f"❌ Ошибка обновления списка команд: {e}")
        import traceback
        traceback.print_exc()


# ==================== Команды ====================

@bot.command(name='ping')
async def ping(ctx):
    """Проверка задержки бота"""
    latency = round(bot.latency * 1000)
    embed = BotTheme.create_embed(
        title=convert_to_font("🏓 понг!"),
        description=convert_to_font(f"задержка: {latency}ms"),
        embed_type='info'
    )
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Список всех команд"""
    embed = BotTheme.create_embed(
        title=convert_to_font("📋 список команд"),
        description=convert_to_font("все команды бота в одном месте!"),
        embed_type='info'
    )
    embed.add_field(
        name=convert_to_font("📍 канал команд"),
        value=f"<#{COMMANDS_CHANNEL_ID}>",
        inline=False
    )
    embed.add_field(
        name=convert_to_font("💡 как использовать"),
        value=convert_to_font("перейди в канал выше чтобы увидеть все команды"),
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='stats')
async def stats(ctx):
    """Статистика бота"""
    if bot.stats['start_time']:
        uptime = datetime.now() - bot.stats['start_time']
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}ч {minutes}м {seconds}с"
    else:
        uptime_str = "Неизвестно"
    
    embed = BotTheme.create_embed(
        title=convert_to_font("📊 статистика бота"),
        embed_type='info'
    )
    embed.timestamp = datetime.now()
    embed.add_field(name=convert_to_font("⏰ аптайм"), value=convert_to_font(uptime_str), inline=True)
    embed.add_field(name=convert_to_font("🌐 серверов"), value=convert_to_font(str(len(bot.guilds))), inline=True)
    embed.add_field(name=convert_to_font("👥 пользователей"), value=convert_to_font(str(len(bot.users))), inline=True)
    embed.add_field(name=convert_to_font("📝 команд использовано"), value=convert_to_font(str(bot.stats['commands_used'])), inline=True)
    embed.add_field(name=convert_to_font("💬 сообщений обработано"), value=convert_to_font(str(bot.stats['messages_seen'])), inline=True)
    embed.add_field(name=convert_to_font("📡 задержка"), value=convert_to_font(f"{round(bot.latency * 1000)}ms"), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='profile')
async def profile(ctx, member: discord.Member = None):
    """Профиль пользователя"""
    member = member or ctx.author
    user = db.get_user(str(member.id))
    
    if not user:
        await ctx.send(convert_to_font("❌ пользователь не найден в базе данных!"))
        return
    
    rank_info = db.get_rank_info(user['rank_id'])
    next_rank = get_next_rank_info(user)
    streak = get_daily_streak(user)
    
    embed = profile_embed(
        title=convert_to_font(f"👤 профиль {member.display_name}")
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name=convert_to_font("🏆 ранг"), value=convert_to_font(rank_info['name']), inline=True)
    embed.add_field(name=convert_to_font("⭐ xp"), value=convert_to_font(str(user['xp'])), inline=True)
    embed.add_field(name=convert_to_font("🔥 серия дней"), value=convert_to_font(str(streak)), inline=True)
    
    if next_rank:
        embed.add_field(
            name=convert_to_font("📈 до следующего ранга"),
            value=convert_to_font(f"{next_rank['xp_needed']} xp\n{next_rank['progress_bar']}"),
            inline=False
        )
    
    if 'games_played' in user:
        win_rate = (user.get('games_won', 0) / user['games_played'] * 100) if user['games_played'] > 0 else 0
        embed.add_field(name=convert_to_font("🎮 игр сыграно"), value=convert_to_font(str(user['games_played'])), inline=True)
        embed.add_field(name=convert_to_font("🏅 побед"), value=convert_to_font(str(user.get('games_won', 0))), inline=True)
        embed.add_field(name=convert_to_font("📊 винрейт"), value=convert_to_font(f"{win_rate:.1f}%"), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='rank')
async def rank(ctx):
    """Текущий ранг пользователя"""
    user = db.get_user(str(ctx.author.id))
    
    if not user:
        await ctx.send(convert_to_font("❌ Ты не зарегистрирован в системе!"))
        return
    
    rank_info = db.get_rank_info(user['rank_id'])
    next_rank = get_next_rank_info(user)
    
    embed = discord.Embed(
        title=convert_to_font(f"🏆 Твой ранг: {rank_info['name']}"),
        color=discord.Color.gold()
    )
    embed.add_field(name=convert_to_font("⭐ XP"), value=convert_to_font(str(user['xp'])), inline=True)
    
    if next_rank:
        embed.add_field(
            name=convert_to_font("📈 До следующего ранга"),
            value=convert_to_font(f"{next_rank['xp_needed']} XP"),
            inline=True
        )
        embed.add_field(
            name=convert_to_font("Прогресс"),
            value=convert_to_font(next_rank['progress_bar']),
            inline=False
        )
    else:
        embed.add_field(name=convert_to_font("🎉"), value=convert_to_font("Максимальный ранг!"), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='top')
async def top(ctx, category: str = 'xp'):
    """Таблица лидеров"""
    category = category.lower()
    
    if category == 'voice':
        # Топ по войсу
        top_users = voice_tracking.get_top_users(10)
        
        if not top_users:
            await ctx.send(convert_to_font("❌ нет данных о войс активности"))
            return
        
        embed = BotTheme.create_embed(
            title=convert_to_font("🎤 топ-10 по войсу"),
            description=convert_to_font("самые активные в голосовых каналах"),
            embed_type='info'
        )
        embed.timestamp = datetime.now()
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, user_data in enumerate(top_users, 1):
            try:
                member = await bot.fetch_user(int(user_data['user_id']))
                medal = medals[idx-1] if idx <= 3 else f"{idx}."
                time_str = voice_tracking.format_time(user_data['total_time'])
                
                embed.add_field(
                    name=convert_to_font(f"{medal} {member.name}"),
                    value=convert_to_font(f"время: {time_str} | сессий: {user_data['sessions_count']}"),
                    inline=False
                )
            except:
                continue
        
        # Добавляем топ каналов
        top_channels = voice_tracking.get_top_channels(3)
        if top_channels:
            channels_text = ""
            for channel_data in top_channels:
                time_str = voice_tracking.format_time(channel_data['total_time'])
                channels_text += f"• {convert_to_font(channel_data['channel_name'])}: {convert_to_font(time_str)}\n"
            
            embed.add_field(
                name=convert_to_font("🔥 топ каналов"),
                value=channels_text,
                inline=False
            )
        
        # Добавляем самую длительную сессию
        longest = voice_tracking.get_longest_session()
        if longest:
            try:
                member = await bot.fetch_user(int(longest['user_id']))
                time_str = voice_tracking.format_time(longest['duration'])
                embed.add_field(
                    name=convert_to_font("⏱️ рекорд сессии"),
                    value=convert_to_font(f"{member.name}: {time_str}"),
                    inline=False
                )
            except:
                pass
        
        await ctx.send(embed=embed)
    
    else:
        # Топ по XP (по умолчанию)
        users = db.get_all_users()
        
        # Сортируем по XP
        sorted_users = sorted(users.items(), key=lambda x: x[1].get('xp', 0), reverse=True)[:10]
        
        embed = BotTheme.create_embed(
            title=convert_to_font("🏆 топ-10 по xp"),
            description=convert_to_font("самые активные игроки"),
            embed_type='info'
        )
        embed.timestamp = datetime.now()
        
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, (user_id, user_data) in enumerate(sorted_users, 1):
            try:
                member = await bot.fetch_user(int(user_id))
                rank_info = db.get_rank_info(user_data['rank_id'])
                medal = medals[idx-1] if idx <= 3 else f"{idx}."
                
                embed.add_field(
                    name=convert_to_font(f"{medal} {member.name}"),
                    value=convert_to_font(f"ранг: {rank_info['name']} | xp: {user_data['xp']}"),
                    inline=False
                )
            except:
                continue
        
        embed.set_footer(text=convert_to_font("используй !top voice для топа по войсу"))
        
        await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily(ctx):
    """Ежедневная награда"""
    user = db.get_user(str(ctx.author.id))
    
    if not user:
        await ctx.send(convert_to_font("❌ ты не зарегистрирован в системе!"))
        return
    
    # Проверяем, можно ли получить награду
    if 'last_daily_date' in user and user['last_daily_date']:
        last_date = datetime.fromisoformat(user['last_daily_date']).date()
        today = datetime.now().date()
        
        if last_date == today:
            next_daily = datetime.combine(today + timedelta(days=1), datetime.min.time())
            time_left = next_daily - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            await ctx.send(convert_to_font(f"⏰ ты уже получил награду сегодня! приходи через {hours}ч {minutes}м"))
            return
    
    # Обновляем серию
    streak = update_daily_streak(user)
    
    # Базовая награда + бонус за серию
    base_reward = 50
    streak_bonus = min(streak * 10, 200)  # Максимум +200 XP
    total_reward = base_reward + streak_bonus
    
    # Сохраняем старый XP
    old_xp = user.get('xp', 0)
    
    # Добавляем XP
    user['xp'] = old_xp + total_reward
    
    # Проверяем повышение ранга
    db.check_rank_up(user)
    
    db.save_user(str(ctx.author.id), user)
    
    # Отправляем базовое сообщение
    embed = BotTheme.create_embed(
        title=convert_to_font("🎁 ежедневная награда получена!"),
        embed_type='success'
    )
    embed.add_field(name=convert_to_font("💰 получено xp"), value=convert_to_font(f"+{total_reward}"), inline=True)
    embed.add_field(name=convert_to_font("🔥 серия дней"), value=convert_to_font(str(streak)), inline=True)
    
    if streak > 1:
        embed.add_field(name=convert_to_font("🎉 бонус за серию"), value=convert_to_font(f"+{streak_bonus} xp"), inline=False)
    
    await ctx.send(embed=embed)
    
    # Роли выдаются автоматически фоновой задачей каждую минуту

@bot.command(name='link')
async def link(ctx):
    """Актуальные ссылки"""
    embed = BotTheme.create_embed(
        title=convert_to_font("🔗 актуальные ссылки"),
        description=convert_to_font("все важные ссылки в одном месте!"),
        embed_type='info'
    )
    embed.add_field(
        name=convert_to_font("🌐 сайт"),
        value="[перейти на сайт](https://bubbly-blessing-production-0c06.up.railway.app/)",
        inline=False
    )
    embed.add_field(
        name=convert_to_font("💬 discord"),
        value="[сервер discord](https://discord.gg/your-invite)",
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='dice')
async def dice(ctx):
    """Бросить кубик (1 раз в час)"""
    user = db.get_user(str(ctx.author.id))
    if not user:
        await ctx.send(convert_to_font("❌ ты не зарегистрирован в системе!"))
        return
    
    # Проверка кулдауна (1 час)
    if 'last_dice' in user and user['last_dice']:
        last_dice = datetime.fromisoformat(user['last_dice'])
        time_diff = (datetime.now() - last_dice).total_seconds()
        
        if time_diff < 3600:  # 1 час
            time_left = 3600 - time_diff
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            await ctx.send(convert_to_font(f"⏰ ты уже бросал кубик! приходи через {hours}ч {minutes}м"))
            return
    
    result = random.randint(1, 6)
    
    # Сохраняем старый XP
    old_xp = user.get('xp', 0)
    
    # Обновляем статистику игр
    user['games_played'] = user.get('games_played', 0) + 1
    
    # Награда за игру
    xp_reward = result * 5
    user['xp'] = old_xp + xp_reward
    
    if result >= 5:
        user['games_won'] = user.get('games_won', 0) + 1
    
    # Сохраняем время последнего броска
    user['last_dice'] = datetime.now().isoformat()
    
    db.save_user(str(ctx.author.id), user)
    
    dice_emoji = ["🎲", "🎲", "🎲", "🎲", "🎲", "🎲"]
    
    embed = game_embed(
        title=convert_to_font("🎲 бросок кубика")
    )
    embed.description = convert_to_font(f"выпало: {dice_emoji[result-1]} {result}")
    embed.add_field(name=convert_to_font("💰 получено xp"), value=convert_to_font(f"+{xp_reward}"), inline=True)
    
    if result >= 5:
        embed.add_field(name=convert_to_font("🎉"), value=convert_to_font("отличный бросок!"), inline=True)
    
    embed.set_footer(text=convert_to_font("следующий бросок через 1 час"))
    
    await ctx.send(embed=embed)
    
    # Роли выдаются автоматически фоновой задачей каждую минуту

@bot.command(name='coinflip')
async def coinflip(ctx, choice: str = None):
    """Подбросить монетку (1 раз в час)"""
    user = db.get_user(str(ctx.author.id))
    if not user:
        await ctx.send(convert_to_font("❌ ты не зарегистрирован в системе!"))
        return
    
    if not choice or choice.lower() not in ['орёл', 'решка', 'орел']:
        await ctx.send(convert_to_font("❌ укажи свой выбор: !coinflip орёл или !coinflip решка"))
        return
    
    # Проверка кулдауна (1 час)
    if 'last_coinflip' in user and user['last_coinflip']:
        last_coinflip = datetime.fromisoformat(user['last_coinflip'])
        time_diff = (datetime.now() - last_coinflip).total_seconds()
        
        if time_diff < 3600:  # 1 час
            time_left = 3600 - time_diff
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            await ctx.send(convert_to_font(f"⏰ ты уже подбрасывал монетку! приходи через {hours}ч {minutes}м"))
            return
    
    result = random.choice(['орёл', 'решка'])
    user_choice = 'орёл' if choice.lower() in ['орёл', 'орел'] else 'решка'
    won = result == user_choice
    
    # Сохраняем старый XP
    old_xp = user.get('xp', 0)
    
    # Обновляем статистику
    user['games_played'] = user.get('games_played', 0) + 1
    
    if won:
        user['games_won'] = user.get('games_won', 0) + 1
        xp_reward = 25
        user['xp'] = old_xp + xp_reward
    else:
        xp_reward = 5
        user['xp'] = old_xp + xp_reward
    
    # Сохраняем время последнего подбрасывания
    user['last_coinflip'] = datetime.now().isoformat()
    
    db.save_user(str(ctx.author.id), user)
    
    embed = game_embed(
        title=convert_to_font("🪙 подбрасывание монетки")
    )
    embed.add_field(name=convert_to_font("твой выбор"), value=convert_to_font(user_choice.capitalize()), inline=True)
    embed.add_field(name=convert_to_font("результат"), value=convert_to_font(result.capitalize()), inline=True)
    embed.add_field(name=convert_to_font("💰 получено xp"), value=convert_to_font(f"+{xp_reward}"), inline=False)
    
    if won:
        embed.description = convert_to_font("🎉 ты выиграл!")
    else:
        embed.description = convert_to_font("😔 ты проиграл...")
    
    embed.set_footer(text=convert_to_font("следующее подбрасывание через 1 час"))
    
    await ctx.send(embed=embed)
    
    # Роли выдаются автоматически фоновой задачей каждую минуту

@bot.command(name='clear')
async def clear(ctx, amount: int = 10):
    """Очистить сообщения (только для администраторов)"""
    if not is_admin(ctx):
        await ctx.send(convert_to_font("❌ у тебя нет прав для использования этой команды!"))
        return
    
    if amount < 1 or amount > 100:
        await ctx.send(convert_to_font("❌ укажи число от 1 до 100!"))
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    
    embed = BotTheme.create_embed(
        title=convert_to_font("🗑️ сообщения удалены"),
        description=convert_to_font(f"удалено сообщений: {len(deleted) - 1}"),
        embed_type='success'
    )
    msg = await ctx.send(embed=embed)
    
    await asyncio.sleep(3)
    await msg.delete()


# ==================== Команды тикетов ====================

@bot.command(name='ticket')
async def ticket(ctx):
    """Создать тикет поддержки"""
    await tickets_system.create_ticket(ctx, bot)

@bot.command(name='close')
async def close(ctx):
    """Закрыть тикет"""
    await tickets_system.close_ticket(ctx, bot)


# ==================== Команды для администраторов ====================

@bot.command(name='updatecommands')
async def update_commands_manual(ctx):
    """
    Обновить список команд в канале вручную
    """
    if not is_admin(ctx):
        await ctx.send(convert_to_font("❌ у тебя нет прав для использования этой команды!"))
        return
    
    try:
        await update_commands_list()
        await ctx.send(convert_to_font("✅ список команд обновлён!"))
    except Exception as e:
        await ctx.send(convert_to_font(f"❌ ошибка: {e}"))

@bot.command(name='setupverification')
async def setup_verification_manual(ctx):
    """
    Настроить систему верификации вручную
    """
    if not is_admin(ctx):
        await ctx.send(convert_to_font("❌ у тебя нет прав для использования этой команды!"))
        return
    
    try:
        success = await verification_system.setup_verification(bot)
        if success:
            await ctx.send(convert_to_font("✅ система верификации настроена!"))
        else:
            await ctx.send(convert_to_font("❌ не удалось настроить верификацию"))
    except Exception as e:
        await ctx.send(convert_to_font(f"❌ ошибка: {e}"))

@bot.command(name='setuptickets')
async def setup_tickets_manual(ctx):
    """
    Настроить кнопку тикетов вручную
    """
    if not is_admin(ctx):
        await ctx.send(convert_to_font("❌ у тебя нет прав для использования этой команды!"))
        return
    
    try:
        success = await tickets_system.setup_ticket_button(bot)
        if success:
            await ctx.send(convert_to_font("✅ кнопка тикетов настроена!"))
        else:
            await ctx.send(convert_to_font("❌ не удалось настроить кнопку"))
    except Exception as e:
        await ctx.send(convert_to_font(f"❌ ошибка: {e}"))

@bot.command(name='setuprankroles')
async def setup_rank_roles(ctx, tier: str = None, role: discord.Role = None):
    """
    Настроить роли для рангов
    Использование: !setuprankroles [F/E/D/C/B/A/S] [@роль]
    Без параметров - показать текущие настройки
    """
    if not is_admin(ctx):
        await ctx.send(convert_to_font("❌ у тебя нет прав для использования этой команды!"))
        return
    
    if not tier and not role:
        # Показать текущие настройки
        config = rank_roles.get_rank_roles_config()
        
        embed = BotTheme.create_embed(
            title=convert_to_font("⚙️ настройка ролей рангов"),
            description=convert_to_font("текущие настройки ролей для каждого ранга"),
            embed_type='info'
        )
        
        for rank_tier in ['F', 'E', 'D', 'C', 'B', 'A', 'S']:
            role_data = config.get(rank_tier, {})
            role_id = role_data.get('role_id') if isinstance(role_data, dict) else role_data
            
            if role_id:
                role_obj = ctx.guild.get_role(role_id)
                if role_obj:
                    required_xp = role_data.get('required_xp', 0) if isinstance(role_data, dict) else 0
                    embed.add_field(
                        name=convert_to_font(f"ранг {rank_tier}"),
                        value=f"{role_obj.mention} ({required_xp} xp)",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name=convert_to_font(f"ранг {rank_tier}"),
                        value=convert_to_font(f"роль не найдена (id: {role_id})"),
                        inline=True
                    )
            else:
                embed.add_field(
                    name=convert_to_font(f"ранг {rank_tier}"),
                    value=convert_to_font("не настроено"),
                    inline=True
                )
        
        embed.add_field(
            name=convert_to_font("📝 как настроить"),
            value=convert_to_font("!setuprankroles [F/E/D/C/B/A/S] [@роль]"),
            inline=False
        )
        
        await ctx.send(embed=embed)
        return
    
    if not tier or not role:
        await ctx.send(convert_to_font("❌ использование: !setuprankroles [F/E/D/C/B/A/S] [@роль]"))
        return
    
    tier = tier.upper()
    
    if tier not in ['F', 'E', 'D', 'C', 'B', 'A', 'S']:
        await ctx.send(convert_to_font("❌ ранг должен быть F, E, D, C, B, A или S"))
        return
    
    # Устанавливаем роль
    success = rank_roles.set_rank_role(tier, role.id)
    
    if success:
        embed = BotTheme.create_embed(
            title=convert_to_font("✅ роль настроена!"),
            embed_type='success'
        )
        embed.add_field(
            name=convert_to_font(f"ранг {tier}"),
            value=role.mention,
            inline=True
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(convert_to_font("❌ ошибка настройки роли"))

@bot.command(name='syncrankroles')
async def sync_rank_roles(ctx):
    """
    Синхронизировать роли всех пользователей с их рангами
    Полезно при первом запуске или после изменения настроек
    """
    if not is_admin(ctx):
        await ctx.send(convert_to_font("❌ у тебя нет прав для использования этой команды!"))
        return
    
    await ctx.send(convert_to_font("🔄 начинаю синхронизацию ролей..."))
    
    try:
        stats = await rank_roles.sync_all_user_roles(bot, db)
        
        embed = BotTheme.create_embed(
            title=convert_to_font("✅ синхронизация завершена!"),
            embed_type='success'
        )
        embed.add_field(
            name=convert_to_font("всего пользователей"),
            value=convert_to_font(str(stats['total'])),
            inline=True
        )
        embed.add_field(
            name=convert_to_font("обновлено"),
            value=convert_to_font(str(stats['updated'])),
            inline=True
        )
        embed.add_field(
            name=convert_to_font("пропущено"),
            value=convert_to_font(str(stats['skipped'])),
            inline=True
        )
        embed.add_field(
            name=convert_to_font("ошибок"),
            value=convert_to_font(str(stats['errors'])),
            inline=True
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(convert_to_font(f"❌ ошибка синхронизации: {e}"))


# ==================== Команды магазина ====================

@bot.command(name='shop')
async def shop(ctx, category: str = 'all'):
    """Магазин предметов"""
    valid_categories = ['all', 'roles', 'boosts', 'cosmetics', 'special']
    
    if category not in valid_categories:
        category = 'all'
    
    embed = shop_system.get_shop_embed_page(category=category)
    await ctx.send(embed=embed)

@bot.command(name='buy')
async def buy(ctx, item_id: str = None):
    """Купить предмет"""
    if not item_id:
        await ctx.send(convert_to_font("❌ укажи id предмета: !buy [id]"))
        return
    
    success, embed = await shop_system.buy_item(ctx, bot, db, item_id)
    await ctx.send(embed=embed)

@bot.command(name='inventory')
async def inventory(ctx, member: discord.Member = None):
    """Инвентарь пользователя"""
    member = member or ctx.author
    user = db.get_user(str(member.id))
    
    if not user:
        await ctx.send(convert_to_font("❌ пользователь не зарегистрирован!"))
        return
    
    embed = shop_system.get_inventory_embed(user, bot)
    await ctx.send(embed=embed)

@bot.command(name='balance')
async def balance(ctx, member: discord.Member = None):
    """Баланс монет"""
    member = member or ctx.author
    user = db.get_user(str(member.id))
    
    if not user:
        await ctx.send(convert_to_font("❌ пользователь не зарегистрирован!"))
        return
    
    embed = profile_embed(
        title=convert_to_font(f"💰 баланс {member.display_name}")
    )
    embed.add_field(
        name=convert_to_font("монеты"),
        value=convert_to_font(str(user.get('coins', 0))),
        inline=True
    )
    embed.add_field(
        name=convert_to_font("xp"),
        value=convert_to_font(str(user.get('xp', 0))),
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='pay')
async def pay(ctx, member: discord.Member = None, amount: int = 0):
    """Перевести монеты другому пользователю"""
    if not member or amount <= 0:
        await ctx.send(convert_to_font("❌ использование: !pay [@пользователь] [сумма]"))
        return
    
    if member == ctx.author:
        await ctx.send(convert_to_font("❌ нельзя перевести монеты самому себе!"))
        return
    
    if member.bot:
        await ctx.send(convert_to_font("❌ нельзя перевести монеты боту!"))
        return
    
    sender = db.get_user(str(ctx.author.id))
    receiver = db.get_user(str(member.id))
    
    if not sender or not receiver:
        await ctx.send(convert_to_font("❌ пользователь не зарегистрирован!"))
        return
    
    if sender['coins'] < amount:
        await ctx.send(convert_to_font(f"❌ недостаточно монет! у тебя: {sender['coins']}"))
        return
    
    # Перевод монет
    sender['coins'] -= amount
    receiver['coins'] = receiver.get('coins', 0) + amount
    
    db.save_user(str(ctx.author.id), sender)
    db.save_user(str(member.id), receiver)
    
    embed = success_embed(
        title=convert_to_font("💸 перевод выполнен!"),
        description=convert_to_font(f"{ctx.author.mention} → {member.mention}")
    )
    embed.add_field(
        name=convert_to_font("сумма"),
        value=convert_to_font(f"{amount} монет"),
        inline=True
    )
    embed.add_field(
        name=convert_to_font("твой баланс"),
        value=convert_to_font(f"{sender['coins']} монет"),
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='work')
async def work(ctx):
    """Поработать и заработать монеты"""
    user = db.get_user(str(ctx.author.id))
    
    if not user:
        await ctx.send(convert_to_font("❌ ты не зарегистрирован!"))
        return
    
    # Проверка кулдауна (1 час)
    if 'last_work' in user and user['last_work']:
        last_work = datetime.fromisoformat(user['last_work'])
        time_diff = (datetime.now() - last_work).total_seconds()
        
        if time_diff < 3600:  # 1 час
            time_left = 3600 - time_diff
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            await ctx.send(convert_to_font(f"⏰ ты уже работал! приходи через {hours}ч {minutes}м"))
            return
    
    # Сохраняем старый XP для проверки повышения роли
    old_xp = user.get('xp', 0)
    
    # Список работ
    jobs = [
        ("программист", "написал код для сайта", 150, 250),
        ("дизайнер", "создал крутой дизайн", 120, 200),
        ("модератор", "почистил чат от спама", 80, 150),
        ("стример", "провёл стрим на 100 зрителей", 200, 300),
        ("музыкант", "записал новый трек", 100, 180),
        ("художник", "нарисовал арт", 90, 170),
        ("писатель", "написал статью", 70, 140),
        ("геймер", "выиграл турнир", 180, 280),
    ]
    
    job_name, job_desc, min_reward, max_reward = random.choice(jobs)
    reward = random.randint(min_reward, max_reward)
    
    # Бонус за ранг (1% за ранг)
    rank_bonus = int(reward * (user['rank_id'] / 100))
    
    # Применяем буст монет
    total_reward = reward + rank_bonus
    total_reward, boost_bonus = shop_system.apply_boost_to_reward(user, 'coins', total_reward)
    
    # Добавляем монеты
    user['coins'] = user.get('coins', 0) + total_reward
    user['last_work'] = datetime.now().isoformat()
    
    db.save_user(str(ctx.author.id), user)
    
    # Создаём embed
    embed = BotTheme.create_embed(
        title=convert_to_font("💼 работа"),
        description=convert_to_font(f"ты поработал как {job_name}"),
        embed_type='info'
    )
    
    embed.add_field(
        name=convert_to_font("что сделал"),
        value=convert_to_font(job_desc),
        inline=False
    )
    
    embed.add_field(
        name=convert_to_font("💰 заработано"),
        value=convert_to_font(f"{total_reward} монет"),
        inline=True
    )
    
    if rank_bonus > 0:
        embed.add_field(
            name=convert_to_font("🎁 бонус за ранг"),
            value=convert_to_font(f"+{rank_bonus} монет"),
            inline=True
        )
    
    if boost_bonus > 0:
        embed.add_field(
            name=convert_to_font("⚡ буст монет"),
            value=convert_to_font(f"+{boost_bonus} монет"),
            inline=True
        )
    
    embed.add_field(
        name=convert_to_font("баланс"),
        value=convert_to_font(f"{user['coins']} монет"),
        inline=False
    )
    
    embed.set_footer(text=convert_to_font("следующая работа через 1 час"))
    
    await ctx.send(embed=embed)
    
    # Роли выдаются автоматически фоновой задачей каждую минуту


# ==================== События для XP ====================

@bot.event
async def on_voice_state_update(member, before, after):
    """Обработка изменения голосового состояния с начислением XP"""
    # Игнорируем ботов
    if member.bot:
        return
    
    # Сохраняем старый XP перед начислением
    user = db.get_user(str(member.id))
    old_xp = user.get('xp', 0)
    
    # Передаём db в voice_tracking для начисления XP
    await voice_tracking.on_voice_state_update(member, before, after, db=db)
    
    # Проверяем выдачу роли только при выходе из войса
    if before.channel is not None and after.channel is None:
        # Пользователь вышел из войса - проверяем роль
        user = db.get_user(str(member.id))
        new_xp = user.get('xp', 0)
        
        if new_xp > old_xp:
            # XP изменился - проверяем роль
            # Создаём фейковый контекст
            class FakeContext:
                def __init__(self, member):
                    self.author = member
                    self.guild = member.guild
                    self.channel = None  # Нет канала для войса
                
                async def send(self, *args, **kwargs):
                    # Отправляем в первый текстовый канал
                    if self.guild:
                        for channel in self.guild.text_channels:
                            try:
                                return await channel.send(*args, **kwargs)
                            except:
                                continue
                    return None
            
            fake_ctx = FakeContext(member)


@bot.event
async def on_message(message):
    """Обработка сообщений с начислением XP"""
    # Игнорируем ботов
    if message.author.bot:
        return
    
    bot.stats['messages_seen'] += 1
    
    # Проверяем, является ли сообщение командой
    if message.content.startswith('!'):
        # Проверяем, в каком канале написана команда
        if commands_channel.is_commands_channel(message.channel.id):
            # В канале команд: обрабатываем и удаляем через 5 минут
            asyncio.create_task(delete_message_after(message, 300))
            await bot.process_commands(message)
        else:
            # В других каналах: отправляем сообщение и удаляем команду
            try:
                # Отправляем сообщение только автору
                warning_msg = await message.channel.send(
                    f"{message.author.mention} " + convert_to_font(f"все команды работают только здесь: <#{commands_channel.COMMANDS_CHANNEL_ID}>")
                )
                # Удаляем команду пользователя сразу
                await message.delete()
                # Удаляем предупреждение через 10 секунд
                asyncio.create_task(delete_message_after(warning_msg, 10))
            except:
                pass
            return
    else:
        # Обычное сообщение (не команда) - начисляем XP
        if voice_tracking.can_earn_message_xp(message.author.id):
            # Рассчитываем XP за сообщение
            xp_reward = voice_tracking.calculate_message_xp(len(message.content))
            
            if xp_reward > 0:
                user = db.get_user(str(message.author.id))
                old_xp = user.get('xp', 0)
                user['xp'] = old_xp + xp_reward
                db.check_rank_up(user)
                db.save_user(str(message.author.id), user)
                
                # Роли выдаются автоматически фоновой задачей каждую минуту
                
                # Логируем
                print(f"💬 {message.author.name} получил {xp_reward} XP за сообщение ({len(message.content)} символов)")
        
        await bot.process_commands(message)


# ==================== Запуск бота ====================

if __name__ == "__main__":
    try:
        bot.run(config.DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
