# Интерактивные Views (кнопки, меню) для Discord бота
import discord
from discord import ui
from font_converter import convert_to_font
from theme import BotTheme
import shop_system

class ShopView(ui.View):
    """View для магазина с кнопками категорий"""
    
    def __init__(self, db, user):
        super().__init__(timeout=180)  # 3 минуты
        self.db = db
        self.user = user
    
    @ui.button(label="Роли", style=discord.ButtonStyle.primary, emoji="🎭")
    async def roles_button(self, interaction: discord.Interaction, button: ui.Button):
        """Показать роли"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Это не твой магазин!", ephemeral=True)
            return
        
        items = shop_system.get_shop_items('roles')
        embed = BotTheme.create_embed(
            title=convert_to_font("🎭 роли"),
            description=convert_to_font("доступные роли:"),
            embed_type='info'
        )
        
        for item in items:
            embed.add_field(
                name=f"{item['emoji']} {convert_to_font(item['name'])}",
                value=convert_to_font(f"💰 {item['price']} монет\n{item['description']}"),
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @ui.button(label="Бусты", style=discord.ButtonStyle.success, emoji="⚡")
    async def boosts_button(self, interaction: discord.Interaction, button: ui.Button):
        """Показать бусты"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Это не твой магазин!", ephemeral=True)
            return
        
        items = shop_system.get_shop_items('boosts')
        embed = BotTheme.create_embed(
            title=convert_to_font("⚡ бусты"),
            description=convert_to_font("доступные бусты:"),
            embed_type='info'
        )
        
        for item in items:
            embed.add_field(
                name=f"{item['emoji']} {convert_to_font(item['name'])}",
                value=convert_to_font(f"💰 {item['price']} монет\n{item['description']}"),
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @ui.button(label="Другое", style=discord.ButtonStyle.secondary, emoji="🎁")
    async def other_button(self, interaction: discord.Interaction, button: ui.Button):
        """Показать другие предметы"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Это не твой магазин!", ephemeral=True)
            return
        
        items = shop_system.get_shop_items('other')
        embed = BotTheme.create_embed(
            title=convert_to_font("🎁 другое"),
            description=convert_to_font("доступные предметы:"),
            embed_type='info'
        )
        
        for item in items:
            embed.add_field(
                name=f"{item['emoji']} {convert_to_font(item['name'])}",
                value=convert_to_font(f"💰 {item['price']} монет\n{item['description']}"),
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @ui.button(label="Купить", style=discord.ButtonStyle.green, emoji="💰", row=1)
    async def buy_button(self, interaction: discord.Interaction, button: ui.Button):
        """Открыть модальное окно для покупки"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Это не твой магазин!", ephemeral=True)
            return
        
        modal = BuyModal(self.db, self.user)
        await interaction.response.send_modal(modal)
    
    @ui.button(label="Закрыть", style=discord.ButtonStyle.danger, emoji="❌", row=1)
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        """Закрыть магазин"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Это не твой магазин!", ephemeral=True)
            return
        
        await interaction.message.delete()


class BuyModal(ui.Modal, title="Купить предмет"):
    """Модальное окно для покупки предмета"""
    
    item_id = ui.TextInput(
        label="ID предмета",
        placeholder="Введи ID предмета (например: color_red)",
        required=True,
        max_length=50
    )
    
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
    
    async def on_submit(self, interaction: discord.Interaction):
        """Обработка покупки"""
        item_id_value = self.item_id.value.strip()
        
        # Покупка через shop_system
        result = shop_system.buy_item(self.db, str(self.user.id), item_id_value)
        
        if result['success']:
            embed = BotTheme.create_embed(
                title=convert_to_font("✅ покупка успешна"),
                description=convert_to_font(f"ты купил: {result['item']['name']}\n💰 потрачено: {result['item']['price']} монет"),
                embed_type='success'
            )
        else:
            embed = BotTheme.create_embed(
                title=convert_to_font("❌ ошибка"),
                description=convert_to_font(result['error']),
                embed_type='error'
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


class TopPaginator(ui.View):
    """Пагинация для таблицы лидеров"""
    
    def __init__(self, pages, current_page=0):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = current_page
        self.update_buttons()
    
    def update_buttons(self):
        """Обновить состояние кнопок"""
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= len(self.pages) - 1
        
        # Обновляем label с номером страницы
        self.page_info.label = f"{self.current_page + 1}/{len(self.pages)}"
    
    @ui.button(label="◀️", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        """Предыдущая страница"""
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @ui.button(label="1/1", style=discord.ButtonStyle.blurple, disabled=True)
    async def page_info(self, interaction: discord.Interaction, button: ui.Button):
        """Информация о странице (не кликабельна)"""
        pass
    
    @ui.button(label="▶️", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        """Следующая страница"""
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @ui.button(label="Закрыть", style=discord.ButtonStyle.danger, emoji="❌", row=1)
    async def close_button(self, interaction: discord.Interaction, button: ui.Button):
        """Закрыть пагинатор"""
        await interaction.message.delete()


class ConfirmView(ui.View):
    """View для подтверждения действия"""
    
    def __init__(self, user, timeout=60):
        super().__init__(timeout=timeout)
        self.user = user
        self.value = None
    
    @ui.button(label="Да", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: ui.Button):
        """Подтвердить"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Это не твоё сообщение!", ephemeral=True)
            return
        
        self.value = True
        self.stop()
        await interaction.response.edit_message(content="✅ Подтверждено", view=None)
    
    @ui.button(label="Нет", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        """Отменить"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Это не твоё сообщение!", ephemeral=True)
            return
        
        self.value = False
        self.stop()
        await interaction.response.edit_message(content="❌ Отменено", view=None)


print("✅ Views (интерактивные кнопки) загружены")
