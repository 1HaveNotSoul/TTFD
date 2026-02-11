"""
TTFD Telegram Bot - Платёжная система
Версия 3.0 - Только магазин и оплата
"""

import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, PreCheckoutQueryHandler
)

# Импорты модулей
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_IDS
from database import db

# Импорты для магазина
from handlers.shop import (
    shop_command, shop_buy_handler, shop_purchases_handler, shop_menu_handler,
    precheckout_callback, successful_payment_callback, PRODUCTS
)

async def start_command(update: Update, context):
    """Команда /start - показать магазин"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # Создаём/обновляем пользователя в БД
    db.update_user(
        telegram_id,
        username=user.username or 'Unknown',
        first_name=user.first_name or 'Unknown'
    )
    
    # Проверяем deep link (например: /start buy_optimizer)
    if context.args:
        deep_link = context.args[0]
        
        # Обработка покупки через deep link
        if deep_link.startswith('buy_'):
            product_id = deep_link.replace('buy_', '')
            
            if product_id in PRODUCTS:
                product = PRODUCTS[product_id]
                
                keyboard = [[
                    InlineKeyboardButton(
                        f"💳 Купить {product['name']} ({product['price']}⭐)",
                        callback_data=f"shop_buy_{product_id}"
                    )
                ], [
                    InlineKeyboardButton("🛍️ Посмотреть все товары", callback_data="shop_menu")
                ]]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = f"🛍️ <b>{product['name']}</b>\n\n"
                message += f"{product['description']}\n\n"
                message += f"💰 Цена: <b>{product['price']} ⭐ Stars</b>"
                
                await update.message.reply_text(
                    message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                return
    
    # Обычный /start - показываем магазин
    keyboard = [[
        InlineKeyboardButton("🛍️ Магазин", callback_data="shop_menu")
    ], [
        InlineKeyboardButton("📦 Мои покупки", callback_data="shop_purchases")
    ]]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🛍️ <b>TTFD Software Shop</b>

Привет, {user.first_name}! 👋

Здесь ты можешь купить программы для оптимизации Windows:

• <b>TTFD Optimizer</b> - 20⭐ Stars
• <b>TTFD Cleaner</b> - 20⭐ Stars  
• <b>TTFD Bundle</b> - 30⭐ Stars (обе программы)

Оплата через Telegram Stars 💫
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def help_command(update: Update, context):
    """Команда /help - справка"""
    help_text = """
📖 <b>Справка</b>

<b>Команды:</b>
/start - Главное меню
/shop - Магазин
/help - Эта справка

<b>Как купить:</b>
1. Выбери продукт
2. Нажми "Купить"
3. Оплати Stars
4. Получи ссылку на скачивание

<b>Продукты:</b>
• TTFD Optimizer - 20⭐
• TTFD Cleaner - 20⭐
• TTFD Bundle - 30⭐

<b>Поддержка:</b>
Если возникли вопросы, напиши @your_support
"""
    
    await update.message.reply_text(help_text, parse_mode='HTML')

def main():
    """Запуск бота"""
    print("=" * 50)
    print("🚀 Запуск TTFD Payment Bot v3.0...")
    print("=" * 50)
    
    # Проверка токена
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == 'your_telegram_bot_token_here':
        print("❌ TELEGRAM_BOT_TOKEN не установлен!")
        print("💡 Получи токен у @BotFather и добавь в .env файл")
        sys.exit(1)
    
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # ========================================================================
    # Регистрируем команды
    # ========================================================================
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("shop", shop_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # ========================================================================
    # Обработчики магазина
    # ========================================================================
    # Кнопки магазина
    app.add_handler(CallbackQueryHandler(shop_buy_handler, pattern="^shop_buy_"))
    app.add_handler(CallbackQueryHandler(shop_purchases_handler, pattern="^shop_purchases$"))
    app.add_handler(CallbackQueryHandler(shop_menu_handler, pattern="^shop_menu$"))
    
    # Обработчики платежей
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    
    print("✅ Обработчики зарегистрированы")
    print("   • Магазин с Telegram Stars")
    print("   • Автоматическая выдача ссылок")
    print("=" * 50)
    print("✅ Payment Bot запущен и готов к работе!")
    print("   Отправь /start боту в Telegram")
    print("=" * 50)
    
    # Запускаем бота
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
