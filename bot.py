# Discord Bot - Основной файл
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime
import config
from database import db

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
        guild = bot.get_guild(config.GUILD_ID)
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
    except Exception as e:
        print(f"❌ Ошибка обновления онлайна: {e}")

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
        ("!help", "Этот список команд"),
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="🎮 Играй в кликер на сайте и получай ранги!")
    await ctx.send(embed=embed)

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
