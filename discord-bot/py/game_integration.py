# Интеграция с TTFD Game
# Система привязки игровых аккаунтов и синхронизации монет

import discord
from discord import app_commands
from discord.ext import commands
import requests
import json
import os
from datetime import datetime
from theme import success_embed, error_embed, warning_embed

# URL API игры
GAME_API_URL = "http://localhost:5000"

# Файл для хранения привязок игровых аккаунтов
GAME_LINKS_FILE = 'json/game_links.json'

class GameIntegration:
    """Класс для работы с интеграцией игры"""
    
    def __init__(self, db):
        self.db = db
        self.game_links = self.load_game_links()
    
    def load_game_links(self):
        """Загрузить привязки игровых аккаунтов"""
        if os.path.exists(GAME_LINKS_FILE):
            with open(GAME_LINKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'links': {}}  # discord_id -> game_code
    
    def save_game_links(self):
        """Сохранить привязки"""
        with open(GAME_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.game_links, f, indent=2, ensure_ascii=False)
    
    def link_game_account(self, discord_id, discord_tag, code):
        """
        Привязать игровой аккаунт к Discord
        
        Args:
            discord_id: Discord ID пользователя
            discord_tag: Discord Tag (username#0000)
            code: 6-значный код из игры
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Отправляем запрос к API игры
            response = requests.post(
                f"{GAME_API_URL}/api/link-account",
                json={
                    'code': code,
                    'discord_id': str(discord_id),
                    'discord_tag': discord_tag
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    # Сохраняем привязку
                    self.game_links['links'][str(discord_id)] = {
                        'code': code,
                        'discord_tag': discord_tag,
                        'linked_at': datetime.now().isoformat()
                    }
                    self.save_game_links()
                    
                    return {
                        'success': True,
                        'message': 'Игровой аккаунт успешно привязан!'
                    }
                else:
                    return {
                        'success': False,
                        'message': data.get('error', 'Неизвестная ошибка')
                    }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'message': 'Неверный код! Проверь код в лаунчере игры.'
                }
            elif response.status_code == 410:
                return {
                    'success': False,
                    'message': 'Код истёк! Коды действуют 10 минут. Сгенерируй новый код.'
                }
            elif response.status_code == 409:
                return {
                    'success': False,
                    'message': 'Код уже использован! Сгенерируй новый код.'
                }
            else:
                return {
                    'success': False,
                    'message': f'Ошибка сервера: {response.status_code}'
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Не удалось подключиться к игровому серверу.\n\nУбедись что API сервер запущен!'
            }
    
    def is_linked(self, discord_id):
        """Проверить привязан ли игровой аккаунт"""
        return str(discord_id) in self.game_links['links']
    
    def get_link_info(self, discord_id):
        """Получить информацию о привязке"""
        return self.game_links['links'].get(str(discord_id))
    
    def add_game_coins(self, discord_id, coins, kills=0, waves=0):
        """
        Добавить монеты из игры пользователю
        
        Args:
            discord_id: Discord ID пользователя
            coins: Количество монет
            kills: Количество убийств
            waves: Количество волн
        
        Returns:
            dict: {'success': bool, 'new_balance': int}
        """
        # Получаем пользователя из БД
        user = self.db.get_user(str(discord_id))
        
        # Добавляем монеты
        old_balance = user.get('coins', 0)
        new_balance = old_balance + coins
        
        # Обновляем баланс
        self.db.update_user(str(discord_id), coins=new_balance)
        
        # Сохраняем статистику игры
        if 'game_stats' not in user:
            user['game_stats'] = {
                'total_coins_earned': 0,
                'total_kills': 0,
                'total_waves': 0,
                'last_sync': None
            }
        
        user['game_stats']['total_coins_earned'] += coins
        user['game_stats']['total_kills'] += kills
        user['game_stats']['total_waves'] += waves
        user['game_stats']['last_sync'] = datetime.now().isoformat()
        
        self.db.save_data()
        
        return {
            'success': True,
            'new_balance': new_balance,
            'coins_added': coins
        }


def setup_game_commands(bot, db, game_integration):
    """Настроить команды для интеграции с игрой"""
    
    # ==================== ПРЕФИКСНАЯ КОМАНДА !contact ====================
    
    @bot.command(name='contact')
    async def contact_game(ctx, code: str = None):
        """Привязать игровой аккаунт TTFD Game через код"""
        
        if not code:
            embed = error_embed(
                "Неверный формат команды!",
                "Используй: `!contact <код>`\n\n"
                "**Как получить код:**\n"
                "1. Открой лаунчер TTFD Game\n"
                "2. Нажми 'ПРИВЯЗАТЬ DISCORD'\n"
                "3. Нажми 'СГЕНЕРИРОВАТЬ КОД'\n"
                "4. Скопируй 6-значный код\n"
                "5. Напиши `!contact <код>` в Discord"
            )
            await ctx.send(embed=embed)
            return
        
        # Проверка формата кода
        if not code.isdigit() or len(code) != 6:
            embed = error_embed(
                "Неверный формат кода!",
                "Код должен состоять из 6 цифр.\n\n"
                "Получи код в лаунчере игры и используй:\n"
                "`!contact <код>`"
            )
            await ctx.send(embed=embed)
            return
        
        # Проверка существующей привязки
        if game_integration.is_linked(ctx.author.id):
            link_info = game_integration.get_link_info(ctx.author.id)
            embed = warning_embed(
                "Аккаунт уже привязан",
                f"Твой Discord уже привязан к игровому аккаунту.\n\n"
                f"Дата привязки: {link_info['linked_at'][:10]}\n\n"
                f"Если хочешь отвязать аккаунт, используй `!unlink`"
            )
            await ctx.send(embed=embed)
            return
        
        # Отправляем сообщение о процессе
        processing_msg = await ctx.send("🔄 Привязываю аккаунт...")
        
        # Привязываем аккаунт
        result = game_integration.link_game_account(
            ctx.author.id,
            str(ctx.author),
            code
        )
        
        if result['success']:
            # Создаём пользователя в БД если его нет
            db.get_user(str(ctx.author.id))
            
            embed = success_embed(
                "✅ Аккаунт успешно привязан!",
                f"Твой Discord аккаунт привязан к TTFD Game!\n\n"
                f"Теперь монеты из игры будут автоматически синхронизироваться с Discord.\n\n"
                f"**Как это работает:**\n"
                f"• Играй в TTFD Shooter\n"
                f"• Зарабатывай монеты (250 убийств = +10 монет, 1 волна = +10 монет)\n"
                f"• При выходе из игры монеты автоматически добавятся на твой Discord баланс\n\n"
                f"Проверить баланс: `!balance`"
            )
            await processing_msg.edit(content=None, embed=embed)
        else:
            embed = error_embed(
                "Ошибка привязки",
                result['message']
            )
            await processing_msg.edit(content=None, embed=embed)
    
    @bot.command(name='unlink')
    async def unlink_game(ctx):
        """Отвязать игровой аккаунт"""
        
        if not game_integration.is_linked(ctx.author.id):
            embed = error_embed(
                "Аккаунт не привязан",
                "Твой Discord не привязан к игровому аккаунту.\n\n"
                "Используй `!contact <код>` для привязки."
            )
            await ctx.send(embed=embed)
            return
        
        # Удаляем привязку
        del game_integration.game_links['links'][str(ctx.author.id)]
        game_integration.save_game_links()
        
        embed = success_embed(
            "Аккаунт отвязан",
            "Игровой аккаунт успешно отвязан от Discord.\n\n"
            "Монеты из игры больше не будут синхронизироваться.\n\n"
            "Чтобы привязать снова, используй `!contact <код>`"
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='sync')
    async def sync_game_coins(ctx):
        """Синхронизировать монеты из игры вручную"""
        
        if not game_integration.is_linked(ctx.author.id):
            embed = error_embed(
                "Аккаунт не привязан",
                "Твой Discord не привязан к игровому аккаунту.\n\n"
                "Используй `!contact <код>` для привязки."
            )
            await ctx.send(embed=embed)
            return
        
        # Отправляем сообщение о процессе
        processing_msg = await ctx.send("🔄 Синхронизирую монеты из игры...")
        
        try:
            # Запрос к API для синхронизации
            response = requests.post(
                f"{GAME_API_URL}/api/sync-coins",
                json={'discord_id': str(ctx.author.id)},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    coins_synced = data.get('coins_synced', 0)
                    new_balance = data.get('new_balance', 0)
                    
                    if coins_synced > 0:
                        # ВАЖНО: Перезагружаем данные бота из файла
                        db.load_data()
                        
                        embed = success_embed(
                            "✅ Монеты синхронизированы!",
                            f"Добавлено монет: **{coins_synced}** 💰\n"
                            f"Новый баланс: **{new_balance}** 💰\n\n"
                            f"Проверить баланс: `!balance`"
                        )
                    else:
                        embed = warning_embed(
                            "Нет монет для синхронизации",
                            "У тебя нет накопленных монет в игре.\n\n"
                            "Играй в TTFD Shooter и зарабатывай монеты!"
                        )
                    
                    await processing_msg.edit(content=None, embed=embed)
                else:
                    embed = error_embed(
                        "Ошибка синхронизации",
                        data.get('error', 'Неизвестная ошибка')
                    )
                    await processing_msg.edit(content=None, embed=embed)
            else:
                embed = error_embed(
                    "Ошибка сервера",
                    f"API сервер вернул ошибку: {response.status_code}"
                )
                await processing_msg.edit(content=None, embed=embed)
        
        except requests.exceptions.RequestException as e:
            embed = error_embed(
                "Ошибка подключения",
                f"Не удалось подключиться к игровому серверу.\n\n"
                f"Убедись что API сервер запущен!\n\n"
                f"Ошибка: {e}"
            )
            await processing_msg.edit(content=None, embed=embed)
    
    # ==================== SLASH КОМАНДЫ (оставляем для совместимости) ====================
    
    @bot.tree.command(name="gamelink", description="Привязать игровой аккаунт TTFD Game")
    @app_commands.describe(code="6-значный код из лаунчера игры")
    async def gamelink_slash(interaction: discord.Interaction, code: str):
        """Привязать игровой аккаунт"""
        
        # Проверка формата кода
        if not code.isdigit() or len(code) != 6:
            embed = error_embed(
                "Неверный формат кода!",
                "Код должен состоять из 6 цифр.\n\n"
                "Получи код в лаунчере игры:\n"
                "1. Открой лаунчер TTFD Game\n"
                "2. Нажми 'ПРИВЯЗАТЬ DISCORD'\n"
                "3. Нажми 'СГЕНЕРИРОВАТЬ КОД'\n"
                "4. Скопируй код и используй `/link <код>`"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Проверка существующей привязки
        if game_integration.is_linked(interaction.user.id):
            link_info = game_integration.get_link_info(interaction.user.id)
            embed = warning_embed(
                "Аккаунт уже привязан",
                f"Твой Discord уже привязан к игровому аккаунту.\n\n"
                f"Дата привязки: {link_info['linked_at'][:10]}\n\n"
                f"Если хочешь отвязать аккаунт, используй `/unlink`"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Отложенный ответ (привязка может занять время)
        await interaction.response.defer(ephemeral=True)
        
        # Привязываем аккаунт
        result = game_integration.link_game_account(
            interaction.user.id,
            str(interaction.user),
            code
        )
        
        if result['success']:
            # Создаём пользователя в БД если его нет
            db.get_user(str(interaction.user.id))
            
            embed = success_embed(
                "✅ Аккаунт успешно привязан!",
                f"Твой Discord аккаунт привязан к TTFD Game!\n\n"
                f"Теперь монеты из игры будут автоматически синхронизироваться с Discord.\n\n"
                f"**Как это работает:**\n"
                f"• Играй в TTFD Shooter\n"
                f"• Зарабатывай монеты (250 убийств = +10 монет, 1 волна = +10 монет)\n"
                f"• При выходе из игры монеты автоматически добавятся на твой Discord баланс\n\n"
                f"Проверить баланс: `/balance`"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = error_embed(
                "Ошибка привязки",
                result['message']
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @bot.tree.command(name="unlinkgame", description="Отвязать игровой аккаунт")
    async def unlink_game(interaction: discord.Interaction):
        """Отвязать игровой аккаунт"""
        
        if not game_integration.is_linked(interaction.user.id):
            embed = error_embed(
                "Аккаунт не привязан",
                "Твой Discord не привязан к игровому аккаунту.\n\n"
                "Используй `/link <код>` для привязки."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Удаляем привязку
        del game_integration.game_links['links'][str(interaction.user.id)]
        game_integration.save_game_links()
        
        embed = success_embed(
            "Аккаунт отвязан",
            "Игровой аккаунт успешно отвязан от Discord.\n\n"
            "Монеты из игры больше не будут синхронизироваться.\n\n"
            "Чтобы привязать снова, используй `/link <код>`"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.command(name="gamestats", description="Статистика из TTFD Game")
    async def game_stats(interaction: discord.Interaction, member: discord.Member = None):
        """Показать статистику из игры"""
        
        target = member or interaction.user
        user = db.get_user(str(target.id))
        
        # Проверка привязки
        if not game_integration.is_linked(target.id):
            embed = error_embed(
                "Аккаунт не привязан",
                f"{'Твой' if target == interaction.user else 'Этот'} Discord не привязан к игровому аккаунту.\n\n"
                "Используй `/link <код>` для привязки."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Получаем статистику
        game_stats = user.get('game_stats', {
            'total_coins_earned': 0,
            'total_kills': 0,
            'total_waves': 0,
            'last_sync': None
        })
        
        # Создаём embed
        embed = discord.Embed(
            title=f"🎮 Статистика TTFD Game",
            description=f"Игровая статистика {target.mention}",
            color=discord.Color.from_rgb(139, 0, 0)
        )
        
        embed.add_field(
            name="💰 Заработано монет",
            value=f"{game_stats['total_coins_earned']:,}",
            inline=True
        )
        
        embed.add_field(
            name="🎯 Убийств",
            value=f"{game_stats['total_kills']:,}",
            inline=True
        )
        
        embed.add_field(
            name="🌊 Волн пройдено",
            value=f"{game_stats['total_waves']:,}",
            inline=True
        )
        
        if game_stats['last_sync']:
            last_sync = datetime.fromisoformat(game_stats['last_sync'])
            embed.add_field(
                name="🔄 Последняя синхронизация",
                value=f"<t:{int(last_sync.timestamp())}:R>",
                inline=False
            )
        
        link_info = game_integration.get_link_info(target.id)
        if link_info:
            linked_at = datetime.fromisoformat(link_info['linked_at'])
            embed.set_footer(text=f"Аккаунт привязан {linked_at.strftime('%d.%m.%Y')}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Экспорт
__all__ = ['GameIntegration', 'setup_game_commands']
