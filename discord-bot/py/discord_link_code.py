"""
Команда /getcode для Discord бота
Генерирует код для привязки Telegram аккаунта
УПРОЩЁННАЯ ВЕРСИЯ - без asyncpg, работает с существующей БД
"""

import discord
from discord import app_commands
import os
from datetime import datetime, timedelta
import secrets
import string
import logging

logger = logging.getLogger(__name__)


def generate_code(length: int = 6) -> str:
    """
    Генерировать криптографически безопасный код
    
    Args:
        length: Длина кода (по умолчанию 6)
    
    Returns:
        Код из заглавных букв и цифр (исключая похожие символы)
    """
    # Исключаем похожие символы: 0/O, 1/I/L
    alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def setup_discord_link_commands(bot, db):
    """Настроить команды привязки для Discord"""
    
    @bot.tree.command(name="getcode", description="Получить код для привязки Telegram аккаунта")
    async def getcode(interaction: discord.Interaction):
        """
        Генерировать код для привязки Telegram
        Код отправляется в личные сообщения и действителен 3 минуты
        """
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        
        # Генерируем код
        code = generate_code(6)
        
        # Сохраняем код в локальной БД Discord (временно, пока не настроим PostgreSQL)
        # Используем существующую систему хранения
        user = db.get_user(discord_id)
        if 'link_code' not in user:
            user['link_code'] = {}
        
        user['link_code'] = {
            'code': code,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(minutes=3)).isoformat(),
            'used': False
        }
        db.save_data()
        
        # Отправляем код в ЛС
        try:
            dm_embed = discord.Embed(
                title="🔗 Код для привязки Telegram",
                description=f"**Твой код:** `{code}`",
                color=discord.Color.green()
            )
            dm_embed.add_field(
                name="📝 Как использовать:",
                value="1. Зайди в Telegram бот\n"
                      f"2. Используй команду `/code {code}`\n"
                      "3. Аккаунты автоматически привяжутся! 🎉",
                inline=False
            )
            dm_embed.add_field(
                name="⏰ Важно:",
                value="Код действителен **3 минуты**",
                inline=False
            )
            dm_embed.set_footer(text=f"Discord ID: {discord_id}")
            
            await interaction.user.send(embed=dm_embed)
            
            # Подтверждение в канале
            await interaction.followup.send(
                "✅ **Код отправлен в личные сообщения!**\n\n"
                "Проверь свои ЛС и используй код в Telegram боте.\n"
                f"Команда: `/code {code}`\n\n"
                "⏰ Код действителен 3 минуты",
                ephemeral=True
            )
            
            logger.info(f"✅ Код {code} сгенерирован для Discord {discord_id}")
        
        except discord.Forbidden:
            # Не удалось отправить в ЛС - показываем код в канале
            embed = discord.Embed(
                title="🔗 Код для привязки Telegram",
                description=f"**Твой код:** `{code}`",
                color=discord.Color.orange()
            )
            embed.add_field(
                name="⚠️ Не удалось отправить в ЛС",
                value="Включи личные сообщения от участников сервера",
                inline=False
            )
            embed.add_field(
                name="📝 Как использовать:",
                value="1. Зайди в Telegram бот\n"
                      f"2. Используй команду `/code {code}`\n"
                      "3. Аккаунты автоматически привяжутся! 🎉",
                inline=False
            )
            embed.add_field(
                name="⏰ Важно:",
                value="Код действителен **3 минуты**",
                inline=False
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.warning(f"⚠️ Не удалось отправить код {code} в ЛС Discord {discord_id}")
    
    
    @bot.tree.command(name="checklink", description="Проверить статус привязки Telegram")
    async def checklink(interaction: discord.Interaction):
        """Проверить привязан ли Telegram аккаунт"""
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        
        # Проверяем привязку в локальной БД
        telegram_id = db.get_telegram_link(discord_id)
        
        if not telegram_id:
            embed = discord.Embed(
                title="❌ Telegram не привязан",
                description="Твой Discord не привязан к Telegram аккаунту",
                color=discord.Color.red()
            )
            embed.add_field(
                name="🔗 Как привязать?",
                value="1. Используй команду `/getcode` здесь в Discord\n"
                      "2. Получи код в личные сообщения\n"
                      "3. Зайди в Telegram бот\n"
                      "4. Используй команду `/code <КОД>`",
                inline=False
            )
        else:
            # Получаем данные пользователя
            user_data = db.get_user(discord_id)
            
            embed = discord.Embed(
                title="✅ Аккаунты привязаны!",
                description="Твои аккаунты синхронизированы",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📱 Telegram",
                value=f"ID: `{telegram_id}`",
                inline=True
            )
            embed.add_field(
                name="💬 Discord",
                value=f"ID: `{discord_id}`\n"
                      f"Username: {interaction.user.name}",
                inline=True
            )
            embed.add_field(
                name="📊 Синхронизированные данные",
                value=f"💰 Монеты: {user_data.get('coins', 0)}\n"
                      f"✨ XP: {user_data.get('xp', 0)}\n"
                      f"⭐ Ранг: #{user_data.get('rank_id', 0)}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    
    @bot.tree.command(name="unlink", description="Отвязать Telegram аккаунт")
    async def unlink(interaction: discord.Interaction):
        """Отвязать Telegram аккаунт от Discord"""
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        
        # Проверяем привязку
        telegram_id = db.get_telegram_link(discord_id)
        
        if not telegram_id:
            await interaction.followup.send(
                "❌ **Telegram не привязан**\n\n"
                "У тебя нет привязанного Telegram аккаунта.",
                ephemeral=True
            )
            return
        
        # Отвязываем
        db.unlink_telegram(discord_id)
        
        embed = discord.Embed(
            title="✅ Telegram отвязан",
            description=f"Telegram ID `{telegram_id}` успешно отвязан от твоего Discord",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🔗 Чтобы привязать снова:",
            value="1. Используй `/getcode` здесь\n"
                  "2. Используй `/code <КОД>` в Telegram боте",
            inline=False
        )
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        logger.info(f"✅ Отвязка: Discord {discord_id} ↔ Telegram {telegram_id}")
    
    logger.info("✅ Discord link code команды настроены (упрощённая версия)")
