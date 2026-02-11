# Команды магазина для добавления в bot.py

"""
Скопируй эти команды в bot.py перед строкой "# ==================== Запуск бота ===================="
"""

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

@bot.command(name='gift')
async def gift(ctx, member: discord.Member = None, amount: int = 0):
    """Подарить монеты другому пользователю"""
    if not member or amount <= 0:
        await ctx.send(convert_to_font("❌ использование: !gift [@пользователь] [сумма]"))
        return
    
    if member == ctx.author:
        await ctx.send(convert_to_font("❌ нельзя подарить монеты самому себе!"))
        return
    
    if member.bot:
        await ctx.send(convert_to_font("❌ нельзя подарить монеты боту!"))
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
        title=convert_to_font("💝 подарок отправлен!"),
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
