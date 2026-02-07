# Slash команды для Discord бота
import discord
from discord import app_commands
from discord.ext import commands
from font_converter import convert_to_font
from theme import BotTheme

async def setup_slash_commands(bot, db):
    """Регистрация всех slash команд"""
    
    @bot.tree.command(name="profile", description="Посмотреть профиль пользователя")
    @app_commands.describe(member="Пользователь (оставь пустым чтобы посмотреть свой)")
    async def profile_slash(interaction: discord.Interaction, member: discord.Member = None):
        """Slash команда для профиля"""
        target = member or interaction.user
        user_data = db.get_user(str(target.id))
        
        embed = BotTheme.create_embed(
            title=convert_to_font(f"📊 профиль {target.name}"),
            embed_type='info'
        )
        
        embed.add_field(
            name=convert_to_font("💎 xp"),
            value=convert_to_font(str(user_data.get('xp', 0))),
            inline=True
        )
        
        embed.add_field(
            name=convert_to_font("💰 монеты"),
            value=convert_to_font(str(user_data.get('coins', 0))),
            inline=True
        )
        
        embed.add_field(
            name=convert_to_font("🎮 игр сыграно"),
            value=convert_to_font(str(user_data.get('games_played', 0))),
            inline=True
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="balance", description="Посмотреть баланс монет")
    @app_commands.describe(member="Пользователь (оставь пустым чтобы посмотреть свой)")
    async def balance_slash(interaction: discord.Interaction, member: discord.Member = None):
        """Slash команда для баланса"""
        target = member or interaction.user
        user_data = db.get_user(str(target.id))
        
        embed = BotTheme.create_embed(
            title=convert_to_font(f"💰 баланс {target.name}"),
            description=convert_to_font(f"монеты: {user_data.get('coins', 0)}"),
            embed_type='success'
        )
        
        embed.set_thumbnail(url=target.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="rank", description="Посмотреть свой ранг")
    async def rank_slash(interaction: discord.Interaction):
        """Slash команда для ранга"""
        user_data = db.get_user(str(interaction.user.id))
        xp = user_data.get('xp', 0)
        rank_id = user_data.get('rank_id', 1)
        
        from database import RANKS
        current_rank = RANKS[rank_id - 1]
        
        # Следующий ранг
        next_rank = RANKS[rank_id] if rank_id < len(RANKS) else None
        
        embed = BotTheme.create_embed(
            title=convert_to_font(f"🏆 твой ранг"),
            embed_type='info'
        )
        
        embed.add_field(
            name=convert_to_font("текущий ранг"),
            value=f"{current_rank['emoji']} {convert_to_font(current_rank['name'])}",
            inline=False
        )
        
        embed.add_field(
            name=convert_to_font("💎 твой xp"),
            value=convert_to_font(str(xp)),
            inline=True
        )
        
        if next_rank:
            xp_needed = next_rank['required_xp'] - xp
            embed.add_field(
                name=convert_to_font(f"до {next_rank['name']}"),
                value=convert_to_font(f"ещё {xp_needed} xp"),
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="top", description="Таблица лидеров")
    @app_commands.describe(category="Категория (xp, coins, games)")
    @app_commands.choices(category=[
        app_commands.Choice(name="XP", value="xp"),
        app_commands.Choice(name="Монеты", value="coins"),
        app_commands.Choice(name="Игры", value="games")
    ])
    async def top_slash(interaction: discord.Interaction, category: str = "xp"):
        """Slash команда для топа"""
        all_users = db.get_all_users()
        
        # Сортировка
        if category == 'xp':
            sorted_users = sorted(all_users.items(), key=lambda x: x[1].get('xp', 0), reverse=True)
            title = "💎 топ по xp"
        elif category == 'coins':
            sorted_users = sorted(all_users.items(), key=lambda x: x[1].get('coins', 0), reverse=True)
            title = "💰 топ по монетам"
        else:
            sorted_users = sorted(all_users.items(), key=lambda x: x[1].get('games_played', 0), reverse=True)
            title = "🎮 топ по играм"
        
        embed = BotTheme.create_embed(
            title=convert_to_font(title),
            embed_type='info'
        )
        
        # Топ 10
        for i, (user_id, user_data) in enumerate(sorted_users[:10], 1):
            try:
                member = interaction.guild.get_member(int(user_id))
                if member:
                    if category == 'xp':
                        value = user_data.get('xp', 0)
                    elif category == 'coins':
                        value = user_data.get('coins', 0)
                    else:
                        value = user_data.get('games_played', 0)
                    
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    embed.add_field(
                        name=f"{medal} {member.name}",
                        value=convert_to_font(str(value)),
                        inline=False
                    )
            except:
                pass
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="shop", description="Открыть магазин")
    async def shop_slash(interaction: discord.Interaction):
        """Slash команда для магазина с кнопками"""
        from views import ShopView
        
        embed = BotTheme.create_embed(
            title=convert_to_font("🏪 магазин"),
            description=convert_to_font("выбери категорию:"),
            embed_type='info'
        )
        
        view = ShopView(db, interaction.user)
        await interaction.response.send_message(embed=embed, view=view)
    
    @bot.tree.command(name="inventory", description="Посмотреть инвентарь")
    @app_commands.describe(member="Пользователь (оставь пустым чтобы посмотреть свой)")
    async def inventory_slash(interaction: discord.Interaction, member: discord.Member = None):
        """Slash команда для инвентаря"""
        target = member or interaction.user
        user_data = db.get_user(str(target.id))
        inventory = user_data.get('inventory', [])
        
        embed = BotTheme.create_embed(
            title=convert_to_font(f"🎒 инвентарь {target.name}"),
            embed_type='info'
        )
        
        if not inventory:
            embed.description = convert_to_font("инвентарь пуст")
        else:
            for item in inventory:
                embed.add_field(
                    name=convert_to_font(item.get('name', 'предмет')),
                    value=convert_to_font(f"количество: {item.get('quantity', 1)}"),
                    inline=True
                )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="daily", description="Получить ежедневную награду")
    async def daily_slash(interaction: discord.Interaction):
        """Slash команда для ежедневной награды"""
        user_data = db.get_user(str(interaction.user.id))
        
        from datetime import datetime, timedelta
        last_daily = user_data.get('last_daily')
        
        if last_daily:
            last_daily_time = datetime.fromisoformat(last_daily)
            time_since = datetime.now() - last_daily_time
            
            if time_since < timedelta(hours=24):
                time_left = timedelta(hours=24) - time_since
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                
                embed = BotTheme.create_embed(
                    title=convert_to_font("⏰ слишком рано"),
                    description=convert_to_font(f"следующая награда через: {hours}ч {minutes}м"),
                    embed_type='error'
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Выдаём награду
        reward_coins = 100
        reward_xp = 50
        
        user_data['coins'] = user_data.get('coins', 0) + reward_coins
        user_data['xp'] = user_data.get('xp', 0) + reward_xp
        user_data['last_daily'] = datetime.now().isoformat()
        
        db.save_user(str(interaction.user.id), user_data)
        
        embed = BotTheme.create_embed(
            title=convert_to_font("🎁 ежедневная награда"),
            description=convert_to_font(f"ты получил:\n💰 {reward_coins} монет\n💎 {reward_xp} xp"),
            embed_type='success'
        )
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name="work", description="Поработать и заработать монеты")
    async def work_slash(interaction: discord.Interaction):
        """Slash команда для работы"""
        user_data = db.get_user(str(interaction.user.id))
        
        from datetime import datetime, timedelta
        import random
        
        last_work = user_data.get('last_work')
        
        if last_work:
            last_work_time = datetime.fromisoformat(last_work)
            time_since = datetime.now() - last_work_time
            
            if time_since < timedelta(hours=1):
                time_left = timedelta(hours=1) - time_since
                minutes = int(time_left.total_seconds() // 60)
                
                embed = BotTheme.create_embed(
                    title=convert_to_font("⏰ ты устал"),
                    description=convert_to_font(f"отдохни ещё {minutes} минут"),
                    embed_type='error'
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        
        # Работа
        reward_coins = random.randint(50, 150)
        reward_xp = random.randint(10, 30)
        
        jobs = [
            "поработал курьером",
            "помог в магазине",
            "убрал мусор",
            "выгулял собак",
            "помыл машины"
        ]
        
        job = random.choice(jobs)
        
        user_data['coins'] = user_data.get('coins', 0) + reward_coins
        user_data['xp'] = user_data.get('xp', 0) + reward_xp
        user_data['last_work'] = datetime.now().isoformat()
        
        db.save_user(str(interaction.user.id), user_data)
        
        embed = BotTheme.create_embed(
            title=convert_to_font("💼 работа"),
            description=convert_to_font(f"ты {job} и заработал:\n💰 {reward_coins} монет\n💎 {reward_xp} xp"),
            embed_type='success'
        )
        
        await interaction.response.send_message(embed=embed)
    
    print("✅ Slash команды зарегистрированы")
