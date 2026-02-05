"""
Тестирование конвертации шрифта
"""

from font_converter import convert_to_font

# Тестовые фразы
test_phrases = [
    "команды бота",
    "КОМАНДЫ БОТА",
    "Команды Бота",
    "проверка задержки",
    "профиль пользователя",
    "мини-игры",
    "модерация",
    "поддержка",
    "администрирование",
]

print("="*70)
print("ТЕСТ КОНВЕРТАЦИИ ШРИФТА")
print("="*70)

for phrase in test_phrases:
    converted = convert_to_font(phrase)
    print(f"\nОригинал:    {phrase}")
    print(f"Конвертация: {converted}")

print("\n" + "="*70)
print("✅ РЕКОМЕНДАЦИЯ: Используйте строчные буквы для лучшего результата!")
print("="*70)
