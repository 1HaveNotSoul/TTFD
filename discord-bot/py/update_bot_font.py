# Скрипт для обновления всех текстовых сообщений бота на новый шрифт

import re

def wrap_strings_in_convert(file_path):
    """Обернуть все строки в функцию convert_to_font"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Паттерны для поиска строк в embed'ах и сообщениях
    patterns = [
        # title="текст"
        (r'title="([^"]+)"', r'title=convert_to_font("\1")'),
        # description="текст"
        (r'description="([^"]+)"', r'description=convert_to_font("\1")'),
        # name="текст"
        (r'name="([^"]+)"', r'name=convert_to_font("\1")'),
        # value="текст"
        (r'value="([^"]+)"', r'value=convert_to_font("\1")'),
        # await ctx.send("текст")
        (r'await ctx\.send\("([^"]+)"\)', r'await ctx.send(convert_to_font("\1"))'),
        # await interaction.response.send_message("текст")
        (r'await interaction\.response\.send_message\("([^"]+)"\)', r'await interaction.response.send_message(convert_to_font("\1"))'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Файл {file_path} обновлён!")

if __name__ == "__main__":
    wrap_strings_in_convert('bot.py')
