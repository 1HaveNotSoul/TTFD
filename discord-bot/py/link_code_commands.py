"""
Команды привязки через код для Discord бота
Использование кода из Telegram для быстрой привязки
"""

import discord
from discord import app_commands
import sys
import os
import logging

# Добавляем путь к shared модулю
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

logger = logging.getLogger(__name__)


async def setup_link_code_commands(bot, db):
    """Настроить команды привязки через код"""
    
    @bot.tree.command(name="link", description="Привязать Telegram аккаунт через код")
    @app_commands.describe(code="Код из Telegram бота (например: ABC123)")
    async def link_code(interaction: discord.Interaction, code: str):
        """
        Привязать Telegram аккаунт через код
        
        Args:
            code: Код из команды /linkcode в Telegram боте
        """
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        code = code.upper().strip()
        
        try:
            from link_codes import get_link_code_manager
            from database_unified import get_unified_db
            
            # Получаем менеджер кодов
            manager = await get_link_code_manager()
            
            # Проверяем код
            code_data = await manager.verify_code(code)
            
            if not code_data:
                await interaction.followup.send(
                    "❌ **Код недействителен**\n\n"
                    "Возможные причины:\n"
                    "• Код неправильный\n"
                    "• Код уже использован\n"
                    "• Код истёк (действителен 10 минут)\n\n"
                    "Получи новый код в Telegram боте: `/linkcode`",
                    ephemeral=True
                )
                return
            
            telegram_id = code_data['telegram_id']
            
            # Используем код
            success = await manager.use_code(code, discord_id)
            
            if not success:
                await interaction.followup.send(
                    "❌ **Не удалось использовать код**\n\n"
                    "Код мог быть использован другим пользователем.\n"
                    "Получи новый код в Telegram боте: `/linkcode`",
                    ephemeral=True
                )
                return
            
            # Привязываем аккаунты в unified database
            try:
                unified_db = await get_unified_db()
                
                # Получаем или создаём пользователей
                tg_user = await unified_db.get_user_by_telegram(telegram_id)
                discord_user = await unified_db.get_user_by_discord(discord_id)
                
                if tg_user and discord_user:
                    # Оба аккаунта существуют - объединяем
                    if tg_user.id != discord_user.id:
                        # Разные аккаунты - нужно объединить данные
                        # Пока просто привязываем Discord к Telegram аккаунту
                        await unified_db.link_discord(tg_user.id, discord_id)
                        
                        embed = discord.Embed(
                            title="✅ Аккаунты привязаны!",
                            description=f"Discord привязан к Telegram аккаунту",
                            color=discord.Color.green()
                        )
                        embed.add_field(
                            name="📊 Данные синхронизированы",
                            value=f"💰 Монеты: {tg_user.coins}\n"
                                  f"✨ XP: {tg_user.xp}\n"
                                  f"⭐ Ранг: #{tg_user.rank_id}",
                            inline=False
                        )
                    else:
                        # Уже привязаны
                        embed = discord.Embed(
                            title="✅ Аккаунты уже привязаны!",
                            description="Твои аккаунты уже синхронизированы",
                            color=discord.Color.blue()
                        )
                        embed.add_field(
                            name="📊 Твои данные",
                            value=f"💰 Монеты: {tg_user.coins}\n"
                                  f"✨ XP: {tg_user.xp}\n"
                                  f"⭐ Ранг: #{tg_user.rank_id}",
                            inline=False
                        )
                
                elif tg_user:
                    # Только Telegram аккаунт существует
                    await unified_db.link_discord(tg_user.id, discord_id)
                    
                    embed = discord.Embed(
                        title="✅ Discord привязан!",
                        description="Твой Discord привязан к Telegram аккаунту",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="📊 Данные из Telegram",
                        value=f"💰 Монеты: {tg_user.coins}\n"
                              f"✨ XP: {tg_user.xp}\n"
                              f"⭐ Ранг: #{tg_user.rank_id}",
                        inline=False
                    )
                
                elif discord_user:
                    # Только Discord аккаунт существует
                    await unified_db.link_telegram(discord_user.id, telegram_id)
                    
                    embed = discord.Embed(
                        title="✅ Telegram привязан!",
                        description="Твой Telegram привязан к Discord аккаунту",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="📊 Данные из Discord",
                        value=f"💰 Монеты: {discord_user.coins}\n"
                              f"✨ XP: {discord_user.xp}\n"
                              f"⭐ Ранг: #{discord_user.rank_id}",
                        inline=False
                    )
                
                else:
                    # Ни один аккаунт не существует - создаём новый
                    user = await unified_db.create_user(
                        telegram_id=telegram_id,
                        discord_id=discord_id,
                        username=interaction.user.name,
                        display_name=interaction.user.display_name or interaction.user.name,
                        primary_platform='discord'
                    )
                    
                    embed = discord.Embed(
                        title="✅ Аккаунты привязаны!",
                        description="Создан новый объединённый аккаунт",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="📊 Начальные данные",
                        value=f"💰 Монеты: {user.coins}\n"
                              f"✨ XP: {user.xp}\n"
                              f"⭐ Ранг: #{user.rank_id}",
                        inline=False
                    )
                
                embed.add_field(
                    name="🎉 Что дальше?",
                    value="Теперь твой баланс синхронизирован между Telegram и Discord!\n"
                          "Зарабатывай монеты на любой платформе - они будут везде одинаковые.",
                    inline=False
                )
                
                # Сохраняем в локальную БД Discord
                db.link_discord(discord_id, telegram_id)
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"✅ Привязка успешна: Discord {discord_id} ↔ Telegram {telegram_id}")
            
            except Exception as e:
                # Unified database недоступна - сохраняем только локально
                db.link_discord(discord_id, telegram_id)
                
                embed = discord.Embed(
                    title="✅ Код использован!",
                    description=f"Discord ID привязан к Telegram (локально)",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="⚠️ Unified database недоступна",
                    value="Привязка сохранена локально.\n"
                          "Для полной синхронизации обратись к администратору.",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.warning(f"⚠️ Unified database недоступна: {e}")
        
        except ImportError:
            await interaction.followup.send(
                "❌ **Система кодов недоступна**\n\n"
                "Link codes модуль не установлен.\n"
                "Обратись к администратору.",
                ephemeral=True
            )
        
        except Exception as e:
            await interaction.followup.send(
                f"❌ **Ошибка привязки**\n\n{str(e)}",
                ephemeral=True
            )
            logger.error(f"❌ Ошибка привязки через код: {e}")
    
    
    @bot.tree.command(name="checklink", description="Проверить статус привязки аккаунтов")
    async def check_link(interaction: discord.Interaction):
        """Проверить статус привязки Telegram и Discord"""
        await interaction.response.defer(ephemeral=True)
        
        discord_id = str(interaction.user.id)
        
        try:
            from database_unified import get_unified_db
            
            unified_db = await get_unified_db()
            user = await unified_db.get_user_by_discord(discord_id)
            
            if not user:
                embed = discord.Embed(
                    title="❌ Аккаунт не привязан",
                    description="Твой Discord не привязан к Telegram",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="🔗 Как привязать?",
                    value="1. Зайди в Telegram бот\n"
                          "2. Используй команду `/linkcode`\n"
                          "3. Получи код\n"
                          "4. Используй `/link <код>` здесь в Discord",
                    inline=False
                )
            
            elif user.telegram_id:
                embed = discord.Embed(
                    title="✅ Аккаунты привязаны!",
                    description="Твои аккаунты синхронизированы",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="📱 Telegram",
                    value=f"ID: `{user.telegram_id}`\n"
                          f"Username: {user.username}",
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
                    value=f"💰 Монеты: {user.coins}\n"
                          f"✨ XP: {user.xp}\n"
                          f"⭐ Ранг: #{user.rank_id}",
                    inline=False
                )
            
            else:
                embed = discord.Embed(
                    title="⚠️ Частичная привязка",
                    description="Discord аккаунт существует, но Telegram не привязан",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="🔗 Привяжи Telegram",
                    value="Используй `/linkcode` в Telegram боте",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(
                f"❌ Ошибка проверки: {str(e)}",
                ephemeral=True
            )
            logger.error(f"❌ Ошибка проверки привязки: {e}")
    
    logger.info("✅ Link code команды настроены для Discord")
