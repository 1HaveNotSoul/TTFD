# Система тикетов поддержки

import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
from datetime import datetime
import json
import os
from font_converter import convert_to_font
from theme import BotTheme, success_embed, error_embed, warning_embed

# ID категории для тикетов
TICKET_CATEGORY_ID = 1466298313975402587

# ID канала для кнопки создания тикетов
TICKET_BUTTON_CHANNEL_ID = 1466298500471062579

# ID роли поддержки
SUPPORT_ROLE_ID = 1467063285559070812

# Файл для хранения ID сообщения с кнопкой
TICKET_MESSAGE_FILE = 'json/ticket_message.json'

# Активные тикеты {user_id: channel_id}
active_tickets = {}


class CreateTicketButton(View):
    """Кнопка для создания тикета"""
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label="🎫 создать тикет", style=discord.ButtonStyle.primary, custom_id="create_ticket_button")
    async def create_ticket_button(self, interaction: discord.Interaction, button: Button):
        """Обработчик нажатия кнопки создания тикета"""
        # Проверяем, есть ли уже активный тикет
        if interaction.user.id in active_tickets:
            existing_channel = self.bot.get_channel(active_tickets[interaction.user.id])
            if existing_channel:
                await interaction.response.send_message(
                    convert_to_font(f"❌ у тебя уже есть тикет: {existing_channel.mention}"),
                    ephemeral=True
                )
                return
            else:
                # Канал удалён, убираем из активных
                del active_tickets[interaction.user.id]
        
        # Отправляем сообщение о создании (только пользователю)
        await interaction.response.send_message(
            convert_to_font("⏳ создаю тикет..."),
            ephemeral=True
        )
        
        # Создаём тикет
        ticket_channel = await create_ticket_for_user(interaction.user, interaction.guild, self.bot)
        
        if ticket_channel:
            # Обновляем сообщение (только пользователю)
            await interaction.edit_original_response(
                content=convert_to_font(f"✅ тикет создан: {ticket_channel.mention}")
            )
        else:
            await interaction.edit_original_response(
                content=convert_to_font("❌ ошибка создания тикета!")
            )


class CloseTicketButton(View):
    """Кнопка для закрытия тикета"""
    def __init__(self, bot, ticket_owner_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_owner_id = ticket_owner_id
    
    @discord.ui.button(label="🔒 закрыть тикет", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        """Обработчик нажатия кнопки закрытия"""
        # Получаем роль поддержки
        support_role = interaction.guild.get_role(SUPPORT_ROLE_ID)
        
        # Проверяем права - ТОЛЬКО роль поддержки может закрывать
        is_support = support_role in interaction.user.roles if support_role else False
        
        if not is_support:
            await interaction.response.send_message(
                convert_to_font("❌ только роль поддержки может закрыть тикет!"),
                ephemeral=True
            )
            return
        
        # Создаём embed с информацией о закрытии
        close_embed = BotTheme.create_embed(
            title=convert_to_font("🔒 закрытие тикета"),
            description=convert_to_font("тикет будет закрыт через 5 секунд..."),
            embed_type='warning'
        )
        close_embed.timestamp = datetime.now()
        
        close_embed.add_field(
            name=convert_to_font("закрыл"),
            value=interaction.user.mention,
            inline=True
        )
        
        if self.ticket_owner_id:
            owner = await self.bot.fetch_user(self.ticket_owner_id)
            close_embed.add_field(
                name=convert_to_font("создатель"),
                value=owner.mention,
                inline=True
            )
        
        await interaction.response.send_message(embed=close_embed)
        
        # Ждём 5 секунд
        await asyncio.sleep(5)
        
        # Удаляем из активных тикетов
        if self.ticket_owner_id and self.ticket_owner_id in active_tickets:
            del active_tickets[self.ticket_owner_id]
        
        # Удаляем канал
        await interaction.channel.delete(reason=f"тикет закрыт пользователем {interaction.user.name}")


async def create_ticket_for_user(user, guild, bot):
    """Создать тикет для пользователя"""
    category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
    
    if not category:
        return None
    
    # Получаем роль поддержки
    support_role = guild.get_role(SUPPORT_ROLE_ID)
    
    # Создаём приватный канал
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            attach_files=True,
            embed_links=True
        ),
        guild.me: discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True
        )
    }
    
    # Добавляем доступ для роли поддержки
    if support_role:
        overwrites[support_role] = discord.PermissionOverwrite(
            read_messages=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
            manage_messages=True
        )
    
    # Создаём канал
    ticket_channel = await guild.create_text_channel(
        name=f"{user.name}",
        category=category,
        overwrites=overwrites,
        topic=f"тикет поддержки | создатель: {user.name}"
    )
    
    # Сохраняем в активные тикеты
    active_tickets[user.id] = ticket_channel.id
    
    # Приветственное сообщение в тикете
    welcome_embed = BotTheme.create_embed(
        title=convert_to_font("🎫 тикет поддержки"),
        description=f"{user.mention}, {convert_to_font('добро пожаловать в поддержку!')}",
        embed_type='ticket'
    )
    welcome_embed.timestamp = datetime.now()
    
    # Формируем текст с упоминанием роли поддержки
    support_mention = f"<@&{SUPPORT_ROLE_ID}>" if support_role else convert_to_font("команда поддержки")
    
    welcome_embed.add_field(
        name=convert_to_font("📝 опиши свою проблему"),
        value=f"{support_mention} {convert_to_font('скоро ответит')}",
        inline=False
    )
    
    welcome_embed.set_footer(
        text=convert_to_font(f"создан пользователем {user.name}"),
        icon_url=user.display_avatar.url
    )
    
    # Создаём кнопку закрытия
    close_button_view = CloseTicketButton(bot, user.id)
    
    await ticket_channel.send(embed=welcome_embed, view=close_button_view)
    
    # Упоминаем роль поддержки
    if support_role:
        await ticket_channel.send(
            f"{support_role.mention} {convert_to_font('- новый тикет!')}",
            delete_after=5
        )
    
    return ticket_channel


async def setup_ticket_button(bot):
    """Настроить кнопку создания тикетов"""
    try:
        channel = bot.get_channel(TICKET_BUTTON_CHANNEL_ID)
        if not channel:
            print(f"⚠️ Канал для кнопки тикетов не найден (ID: {TICKET_BUTTON_CHANNEL_ID})")
            return False
        
        # Проверяем, есть ли сохранённое сообщение
        message_id = load_ticket_message_id()
        
        if message_id:
            try:
                # Пытаемся найти существующее сообщение
                message = await channel.fetch_message(message_id)
                print(f"✅ Кнопка тикетов уже существует (Message ID: {message_id})")
                print(f"   Не создаю новое сообщение - использую существующее")
                
                # Обновляем view на случай перезапуска бота
                view = CreateTicketButton(bot)
                await message.edit(view=view)
                print(f"✅ View кнопки тикетов обновлён")
                
                # Удаляем все ДРУГИЕ сообщения бота в канале (кроме текущего)
                try:
                    deleted_count = 0
                    async for msg in channel.history(limit=100):
                        if msg.author == bot.user and msg.id != message_id:
                            await msg.delete()
                            deleted_count += 1
                            await asyncio.sleep(0.5)
                    if deleted_count > 0:
                        print(f"🗑️ Удалено {deleted_count} старых сообщений тикетов")
                except Exception as e:
                    print(f"⚠️ Ошибка очистки старых сообщений: {e}")
                
                return True
            except discord.NotFound:
                print("⚠️ Старое сообщение не найдено, создаю новое")
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
        
        # Создаём embed с инструкцией
        embed = BotTheme.create_embed(
            title=convert_to_font("🎫 система поддержки"),
            description=convert_to_font("нужна помощь? создай тикет!"),
            embed_type='info'
        )
        
        embed.add_field(
            name=convert_to_font("📝 как это работает?"),
            value=convert_to_font(
                "1. нажми кнопку ниже\n"
                "2. для тебя создастся приватный канал\n"
                "3. опиши свою проблему\n"
                f"4. <@&{SUPPORT_ROLE_ID}> скоро ответит"
            ),
            inline=False
        )
        
        embed.add_field(
            name=convert_to_font("⚠️ правила"),
            value=convert_to_font(
                "• не спамь тикетами\n"
                "• будь вежлив с поддержкой"
            ),
            inline=False
        )
        
        embed.set_footer(text=convert_to_font("нажми кнопку чтобы создать тикет"))
        
        # Создаём кнопку
        view = CreateTicketButton(bot)
        
        # Отправляем сообщение
        message = await channel.send(embed=embed, view=view)
        
        # Сохраняем ID сообщения
        save_ticket_message_id(message.id)
        
        print(f"✅ Кнопка тикетов создана (Message ID: {message.id})")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настройки кнопки тикетов: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_ticket_message_id():
    """Загрузить ID сообщения с кнопкой"""
    try:
        if os.path.exists(TICKET_MESSAGE_FILE):
            with open(TICKET_MESSAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('message_id')
    except Exception as e:
        print(f"⚠️ Не удалось загрузить ID сообщения тикетов: {e}")
    return None


def save_ticket_message_id(message_id):
    """Сохранить ID сообщения с кнопкой"""
    try:
        os.makedirs('json', exist_ok=True)
        data = {
            'message_id': message_id,
            'channel_id': TICKET_BUTTON_CHANNEL_ID,
            'last_updated': datetime.now().isoformat()
        }
        with open(TICKET_MESSAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Сохранён ID сообщения тикетов: {message_id}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить ID сообщения: {e}")


async def create_ticket(ctx, bot):
    """Создать тикет поддержки (старая команда для совместимости)"""
    # Проверяем, есть ли уже активный тикет
    if ctx.author.id in active_tickets:
        existing_channel = bot.get_channel(active_tickets[ctx.author.id])
        if existing_channel:
            embed = error_embed(
                title=convert_to_font("❌ у тебя уже есть тикет"),
                description=f"{convert_to_font('твой тикет:')} {existing_channel.mention}"
            )
            await ctx.send(embed=embed, delete_after=10)
            return None
        else:
            # Канал удалён, убираем из активных
            del active_tickets[ctx.author.id]
    
    # Создаём тикет
    ticket_channel = await create_ticket_for_user(ctx.author, ctx.guild, bot)
    
    if ticket_channel:
        # Уведомление в основном канале
        embed = success_embed(
            title=convert_to_font("🎫 тикет создан"),
            description=f"{convert_to_font('твой тикет:')} {ticket_channel.mention}"
        )
        await ctx.send(embed=embed, delete_after=15)
    
    return ticket_channel


async def close_ticket(ctx, bot):
    """Закрыть тикет (команда !close)"""
    # Проверяем, что команда используется в канале тикета
    # Проверяем по активным тикетам
    is_ticket_channel = False
    ticket_owner = None
    
    for user_id, channel_id in active_tickets.items():
        if channel_id == ctx.channel.id:
            is_ticket_channel = True
            ticket_owner = user_id
            break
    
    if not is_ticket_channel:
        embed = error_embed(
            title=convert_to_font("❌ ошибка"),
            description=convert_to_font("эта команда работает только в каналах тикетов!")
        )
        await ctx.send(embed=embed, delete_after=10)
        return False
    
    # Получаем роль поддержки
    support_role = ctx.guild.get_role(SUPPORT_ROLE_ID)
    
    # Проверяем права - ТОЛЬКО роль поддержки может закрывать
    is_support = support_role in ctx.author.roles if support_role else False
    
    if not is_support:
        embed = error_embed(
            title=convert_to_font("❌ нет прав"),
            description=convert_to_font("только роль поддержки может закрыть тикет!")
        )
        await ctx.send(embed=embed, delete_after=10)
        return False
    
    # Создаём embed с информацией о закрытии
    close_embed = warning_embed(
        title=convert_to_font("🔒 закрытие тикета"),
        description=convert_to_font("тикет будет закрыт через 5 секунд...")
    )
    close_embed.timestamp = datetime.now()
    
    close_embed.add_field(
        name=convert_to_font("закрыл"),
        value=ctx.author.mention,
        inline=True
    )
    
    if ticket_owner:
        owner = await bot.fetch_user(ticket_owner)
        close_embed.add_field(
            name=convert_to_font("создатель"),
            value=owner.mention,
            inline=True
        )
    
    await ctx.send(embed=close_embed)
    
    # Ждём 5 секунд
    await asyncio.sleep(5)
    
    # Удаляем из активных тикетов
    if ticket_owner and ticket_owner in active_tickets:
        del active_tickets[ticket_owner]
    
    # Удаляем канал
    await ctx.channel.delete(reason=f"тикет закрыт пользователем {ctx.author.name}")
    
    return True
