# Discord Bot - Основной файл
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
import config

# Пытаемся использовать PostgreSQL, если нет - JSON
try:
    from database_postgres import db
    print("✅ Используется PostgreSQL")
except Exception as e:
    from database import db
    print(f"⚠️ Используется JSON файл: {e}")

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

# Хранилище активных тикетов
active_tickets = {}

# ID категории для тикетов (будет создана автоматически)
TICKET_CATEGORY_ID = None

# Роли с доступом к тикетам (можно настроить)
SUPPORT_ROLES = ['ADMIN', 'MODERATOR', 'SUPPORT', 'Администратор', 'Модератор']

# ==================== СОБЫТИЯ ====================

@bot.event
async def on_ready():
    """Событие: бот готов к работе"""
    bot.stats['start_time'] = datetime.now()
    
    print("=" * 50)
    print(f"✅ Бот успешно запущен!")
    print(f"📛 Имя: {bot.user}")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🌐 Серверов: {len(bot.guilds)}")
    print(f"👥 Пользователей: {len(bot.users)}")
    print("=" * 50)
    
    # Устанавливаем статус бота
    await bot.change_presence(
        activity=discord.Game(name="!help | Кликер на сайте!"),
        status=discord.Status.online
    )
    
    # Синхронизируем slash команды (если есть)
    try:
        synced = await bot.tree.sync()
        if len(synced) > 0:
            print(f"✅ Синхронизировано {len(synced)} slash команд")
        else:
            print("ℹ️ Slash команды отключены (используются только ! команды)")
    except Exception as e:
        print(f"❌ Ошибка синхронизации команд: {e}")
    
    # Запускаем обновление онлайна
    update_online_members.start()

@bot.event
async def on_message(message):
    """Событие: новое сообщение"""
    # Игнорируем сообщения от ботов
    if message.author.bot:
        return
    
    bot.stats['messages_seen'] += 1
    
    # Даём 1 XP за сообщение
    db.add_xp(str(message.author.id), 1)
    
    # Обрабатываем команды
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    """Событие: команда использована"""
    bot.stats['commands_used'] += 1

@bot.event
async def on_member_join(member):
    """Событие: новый участник присоединился"""
    # Создаём пользователя в базе
    user = db.get_user(str(member.id))
    user['username'] = member.name
    db.save_data()
    
    # Приветственное сообщение
    channel = member.guild.system_channel
    if channel:
        embed = discord.Embed(
            title="👋 Добро пожаловать!",
            description=f"Привет, {member.mention}!\n\n🎮 Играй в кликер на сайте и получай ранги!\n💎 Выполняй задания и зарабатывай монеты!",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

# ==================== ЗАДАЧИ ====================

@tasks.loop(seconds=30)
async def update_online_members():
    """Обновление списка онлайн пользователей"""
    try:
        # Пытаемся получить гильдию по ID, если он установлен
        guild = None
        if config.GUILD_ID and config.GUILD_ID > 0:
            guild = bot.get_guild(config.GUILD_ID)
        
        # Если не нашли по ID, берём первую доступную гильдию
        if not guild and len(bot.guilds) > 0:
            guild = bot.guilds[0]
            print(f"ℹ️ Используется сервер: {guild.name} (ID: {guild.id})")
        
        if guild:
            online_members = []
            for member in guild.members:
                if not member.bot and member.status != discord.Status.offline:
                    online_members.append({
                        'id': str(member.id),
                        'name': member.name,
                        'display_name': member.display_name,
                        'avatar': str(member.display_avatar.url),
                        'status': str(member.status),
                        'activity': str(member.activity.name) if member.activity else None
                    })
            
            # Обновляем данные для веб-сайта
            import web
            web.bot_data['online_members'] = online_members
            web.bot_data['guild_name'] = guild.name
            web.bot_data['guild_id'] = guild.id
        else:
            print("⚠️ Не найдено ни одного сервера")
    except Exception as e:
        print(f"❌ Ошибка обновления онлайна: {e}")
        import traceback
        traceback.print_exc()

# ==================== КОМАНДЫ ====================

@bot.command(name='ping')
async def ping(ctx):
    """Проверка задержки бота"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 иди нахуй!",
        description=f"Задержка: **{latency}ms**",
        color=discord.Color.blue()
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
    
    embed = discord.Embed(
        title="📊 Статистика бота",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    embed.add_field(name="⏱️ Аптайм", value=uptime_str, inline=True)
    embed.add_field(name="🌐 Серверов", value=len(bot.guilds), inline=True)
    embed.add_field(name="👥 Пользователей", value=len(bot.users), inline=True)
    embed.add_field(name="📝 Команд использовано", value=bot.stats['commands_used'], inline=True)
    embed.add_field(name="💬 Сообщений обработано", value=bot.stats['messages_seen'], inline=True)
    embed.add_field(name="📡 Задержка", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='profile')
async def profile(ctx, member: discord.Member = None):
    """Профиль пользователя"""
    member = member or ctx.author
    user = db.get_user(str(member.id))
    user['username'] = member.name
    db.save_data()
    
    rank = db.get_rank_info(user['rank_id'])
    
    # Следующий ранг
    next_rank = None
    xp_needed = 0
    if user['rank_id'] < len(db.get_all_ranks()):
        next_rank = db.get_all_ranks()[user['rank_id']]
        xp_needed = next_rank['required_xp'] - user['xp']
    
    embed = discord.Embed(
        title=f"👤 Профиль {member.name}",
        color=int(rank['color'].replace('#', '0x'), 16),
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    
    embed.add_field(name="🏆 Ранг", value=f"{rank['name']}", inline=True)
    embed.add_field(name="⭐ Опыт", value=f"{user['xp']} XP", inline=True)
    embed.add_field(name="💰 Монеты", value=f"{user['coins']}", inline=True)
    embed.add_field(name="🖱️ Кликов", value=f"{user['clicks']}", inline=True)
    embed.add_field(name="✅ Заданий", value=f"{user['tasks_completed']}", inline=True)
    
    if next_rank:
        embed.add_field(name="📈 До следующего ранга", value=f"{xp_needed} XP", inline=False)
    
    embed.set_footer(text="Играй в кликер на сайте!")
    
    await ctx.send(embed=embed)

@bot.command(name='rank')
async def rank(ctx):
    """Информация о текущем ранге"""
    user = db.get_user(str(ctx.author.id))
    rank = db.get_rank_info(user['rank_id'])
    
    embed = discord.Embed(
        title=f"🏆 Ранг: {rank['name']}",
        description=f"Твой текущий ранг",
        color=int(rank['color'].replace('#', '0x'), 16)
    )
    embed.add_field(name="⭐ Опыт", value=f"{user['xp']} XP", inline=True)
    embed.add_field(name="💰 Монеты", value=f"{user['coins']}", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='top')
async def top(ctx):
    """Таблица лидеров"""
    leaders = db.get_leaderboard(10)
    
    embed = discord.Embed(
        title="🏆 Топ-10 игроков",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, user_data in enumerate(leaders):
        medal = medals[i] if i < 3 else f"{i+1}."
        rank = db.get_rank_info(user_data['rank_id'])
        
        # Пытаемся получить Discord пользователя для отображения имени
        username = user_data.get('username', 'Unknown')
        try:
            discord_user = await bot.fetch_user(int(user_data['id']))
            username = discord_user.name
        except:
            pass
        
        embed.add_field(
            name=f"{medal} {username}",
            value=f"Ранг: {rank['name']} | XP: {user_data['xp']} | Монеты: {user_data['coins']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily(ctx):
    """Ежедневная награда"""
    result = db.claim_daily(str(ctx.author.id))
    
    if result['success']:
        embed = discord.Embed(
            title="🎁 Ежедневная награда!",
            description=f"Ты получил:\n⭐ {result['xp']} XP\n💰 {result['coins']} монет",
            color=discord.Color.green()
        )
        embed.set_footer(text="Возвращайся завтра за новой наградой!")
    else:
        embed = discord.Embed(
            title="⏰ Слишком рано!",
            description=result['error'],
            color=discord.Color.red()
        )
    
    await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Список команд"""
    embed = discord.Embed(
        title="📚 Список команд",
        description="Доступные команды бота",
        color=discord.Color.blue()
    )
    
    commands_list = [
        ("!ping", "Проверка задержки бота"),
        ("!stats", "Статистика бота"),
        ("!profile [@user]", "Профиль пользователя"),
        ("!rank", "Твой текущий ранг"),
        ("!top", "Таблица лидеров"),
        ("!daily", "Ежедневная награда"),
        ("!link", "Ссылка на сайт"),
        ("!ticket", "Создать тикет поддержки"),
        ("!close", "Закрыть тикет (только в канале тикета)"),
        ("!clear <число>", "Очистить сообщения (только для модераторов)"),
        ("!help", "Этот список команд"),
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="🎮 Играй в кликер на сайте и получай ранги!")
    await ctx.send(embed=embed)

@bot.command(name='link')
async def link_command(ctx):
    """Ссылка на сайт"""
    embed = discord.Embed(
        title="🌐 Сайт TTFD",
        description="Играй в игры и зарабатывай ранги!",
        color=discord.Color.blue(),
        url="https://ttfd.onrender.com/"
    )
    
    embed.add_field(
        name="🎮 Игры",
        value="[Все игры](https://ttfd.onrender.com/games)\n"
              "[Змейка](https://ttfd.onrender.com/snake)\n"
              "[Кликер](https://ttfd.onrender.com/game)",
        inline=True
    )
    
    embed.add_field(
        name="📊 Статистика",
        value="[Таблица лидеров](https://ttfd.onrender.com/leaderboard)\n"
              "[Ранги](https://ttfd.onrender.com/ranks)",
        inline=True
    )
    
    embed.add_field(
        name="👤 Аккаунт",
        value="[Вход](https://ttfd.onrender.com/login)\n"
              "[Регистрация](https://ttfd.onrender.com/register)",
        inline=True
    )
    
    embed.set_footer(text="✨ Войди через Discord одним кликом!")
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    await ctx.send(embed=embed)

# ==================== ТИКЕТ-СИСТЕМА ====================

async def get_or_create_ticket_category(guild):
    """Получить или создать категорию для тикетов"""
    global TICKET_CATEGORY_ID
    
    # Ищем существующую категорию
    if TICKET_CATEGORY_ID:
        category = guild.get_channel(TICKET_CATEGORY_ID)
        if category:
            return category
    
    # Ищем категорию по имени
    for category in guild.categories:
        if category.name.lower() == "тикеты" or category.name.lower() == "tickets":
            TICKET_CATEGORY_ID = category.id
            return category
    
    # Создаём новую категорию
    try:
        category = await guild.create_category("🎫 Тикеты")
        TICKET_CATEGORY_ID = category.id
        print(f"✅ Создана категория для тикетов: {category.name}")
        return category
    except Exception as e:
        print(f"❌ Ошибка создания категории: {e}")
        return None

def has_support_role(member):
    """Проверить есть ли у пользователя роль поддержки"""
    if member.guild_permissions.administrator:
        return True
    
    for role in member.roles:
        if role.name in SUPPORT_ROLES or role.name.upper() in SUPPORT_ROLES:
            return True
    
    return False

@bot.command(name='ticket')
async def create_ticket(ctx):
    """Создать тикет поддержки"""
    # Проверяем что команда использована на сервере
    if not ctx.guild:
        await ctx.send("❌ Эта команда доступна только на сервере!")
        return
    
    # Проверяем что у пользователя ещё нет открытого тикета
    user_id = str(ctx.author.id)
    if user_id in active_tickets:
        ticket_channel = ctx.guild.get_channel(active_tickets[user_id])
        if ticket_channel:
            await ctx.send(f"❌ У тебя уже есть открытый тикет: {ticket_channel.mention}")
            return
        else:
            # Канал был удалён, убираем из списка
            del active_tickets[user_id]
    
    # Получаем или создаём категорию
    category = await get_or_create_ticket_category(ctx.guild)
    if not category:
        await ctx.send("❌ Не удалось создать категорию для тикетов!")
        return
    
    # Создаём канал для тикета
    ticket_number = len(active_tickets) + 1
    channel_name = f"ticket-{ctx.author.name}-{ticket_number}"
    
    try:
        # Настройка прав доступа
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            ),
            ctx.guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True
            )
        }
        
        # Добавляем роли поддержки
        for role in ctx.guild.roles:
            if role.name in SUPPORT_ROLES or role.name.upper() in SUPPORT_ROLES or role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True
                )
        
        # Создаём канал
        ticket_channel = await ctx.guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Тикет поддержки для {ctx.author.name}"
        )
        
        # Сохраняем в список активных
        active_tickets[user_id] = ticket_channel.id
        
        # Отправляем сообщение в новый канал
        embed = discord.Embed(
            title="🎫 Тикет создан!",
            description=f"Привет, {ctx.author.mention}!\n\n"
                       f"Опиши свою проблему или вопрос.\n"
                       f"Администрация скоро ответит.\n\n"
                       f"Чтобы закрыть тикет, используй команду `!close`",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Тикет #{ticket_number}")
        
        await ticket_channel.send(embed=embed)
        
        # Уведомляем пользователя
        await ctx.send(f"✅ Тикет создан: {ticket_channel.mention}")
        
        # Уведомляем поддержку
        support_mention = ""
        for role in ctx.guild.roles:
            if role.name in SUPPORT_ROLES or role.name.upper() in SUPPORT_ROLES:
                support_mention += f"{role.mention} "
        
        if support_mention:
            await ticket_channel.send(f"📢 {support_mention} Новый тикет от {ctx.author.mention}!")
        
        print(f"✅ Создан тикет: {channel_name} для {ctx.author.name}")
        
    except Exception as e:
        await ctx.send(f"❌ Ошибка создания тикета: {e}")
        print(f"❌ Ошибка создания тикета: {e}")

@bot.command(name='close')
async def close_ticket(ctx):
    """Закрыть тикет"""
    # Проверяем что команда использована в канале тикета
    if not ctx.channel.name.startswith('ticket-'):
        await ctx.send("❌ Эта команда работает только в каналах тикетов!")
        return
    
    # Проверяем права (создатель тикета или поддержка)
    user_id = str(ctx.author.id)
    is_ticket_owner = user_id in active_tickets and active_tickets[user_id] == ctx.channel.id
    is_support = has_support_role(ctx.author)
    
    if not (is_ticket_owner or is_support):
        await ctx.send("❌ У тебя нет прав закрыть этот тикет!")
        return
    
    # Отправляем сообщение о закрытии
    embed = discord.Embed(
        title="🔒 Тикет закрывается...",
        description="Канал будет удалён через 5 секунд.",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_footer(text=f"Закрыл: {ctx.author.name}")
    
    await ctx.send(embed=embed)
    
    # Удаляем из списка активных
    for uid, channel_id in list(active_tickets.items()):
        if channel_id == ctx.channel.id:
            del active_tickets[uid]
            break
    
    # Ждём 5 секунд и удаляем канал
    await asyncio.sleep(5)
    
    try:
        await ctx.channel.delete(reason=f"Тикет закрыт пользователем {ctx.author.name}")
        print(f"✅ Тикет закрыт: {ctx.channel.name}")
    except Exception as e:
        print(f"❌ Ошибка удаления канала: {e}")

# ==================== КОМАНДА ОЧИСТКИ ====================

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = None):
    """Очистить сообщения в канале"""
    # Проверка что число указано
    if amount is None:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Укажи количество сообщений для удаления!\n\n"
                       "Пример: `!clear 50`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
        return
    
    # Проверка что число положительное
    if amount <= 0:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Количество сообщений должно быть больше 0!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
        return
    
    # Ограничение Discord API - максимум 100 сообщений
    if amount > 100:
        embed = discord.Embed(
            title="⚠️ Предупреждение",
            description=f"Максимум можно удалить 100 сообщений за раз.\n"
                       f"Будет удалено 100 сообщений вместо {amount}.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, delete_after=5)
        amount = 100
    
    try:
        # Удаляем сообщения (+1 для команды)
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        # Отправляем сообщение об успехе
        embed = discord.Embed(
            title="🧹 Чат очищен",
            description=f"Удалено **{len(deleted) - 1}** сообщений",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Модератор: {ctx.author.name}")
        
        # Сообщение автоудаляется через 5 секунд
        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
        
        print(f"✅ Очищено {len(deleted) - 1} сообщений в #{ctx.channel.name} пользователем {ctx.author.name}")
        
    except discord.Forbidden:
        embed = discord.Embed(
            title="❌ Ошибка",
            description="У бота нет прав на удаление сообщений!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
    except discord.HTTPException as e:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=f"Не удалось удалить сообщения: {e}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)

@clear_messages.error
async def clear_error(ctx, error):
    """Обработка ошибок команды clear"""
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Нет прав",
            description="У тебя нет прав на управление сообщениями!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Укажи корректное число!\n\n"
                       "Пример: `!clear 50`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)
    else:
        embed = discord.Embed(
            title="❌ Ошибка",
            description=f"Произошла ошибка: {error}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=5)

# ==================== SLASH КОМАНДЫ ====================
# Slash команды убраны чтобы избежать дублирования с обычными командами

# ==================== ЗАПУСК ====================

def run_bot():
    """Запуск бота"""
    try:
        bot.run(config.DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == "__main__":
    run_bot()
