#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест форматирования обновлений
"""

from font_converter import convert_to_font

# Тестовые изменения
changes = [
    "Настроена система тикетов",
    "Добавлены команды !ticket, !close, !add, !remove",
    "Обновлена структура проекта"
]

print("=" * 60)
print("ТЕСТ ФОРМАТИРОВАНИЯ ОБНОВЛЕНИЙ")
print("=" * 60)

print("\n1. Старый формат (маркер конвертируется):")
for change in changes:
    print(convert_to_font(f"• {change}"))

print("\n2. Новый формат (маркер остаётся обычным):")
for change in changes:
    print(f"• {convert_to_font(change)}")

print("\n3. Полный текст списка изменений:")
changes_text = "\n".join([f"• {convert_to_font(change)}" for change in changes])
print(changes_text)

print("\n" + "=" * 60)
print("✅ Тест завершён")
print("=" * 60)
