"""
Обработчики магазина с Telegram Stars
"""

import secrets
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from database import db
from config import TELEGRAM_ADMIN_IDS

# Продукты для продажи
PRODUCTS = {
    'optimizer': {
        'name': 'TTFD Optimizer',
        'description': '🚀 Оптимизация Windows\n✅ Очистка реестра\n✅ Ускорение системы\n✅ Диагностика',
        'price': 20,  # Stars
        'download_url': 'https://drive.google.com/file/d/1E2f4j8xv4lLeMIqz-1qTWiwaYrfrKSdP/view'
    },
    'cleaner': {
        'name': 'TTFD Cleaner',
        'description': '🧹 Глубокая очистка Windows\n✅ Удаление мусора\n✅ Очистка браузеров\n✅ Автозадачи',
        'price': 20,  # Stars
        'download_url': 'https://drive.google.com/file/d/1Cxu2yoNw9E2OG3jdyi8KVtPTtvF0zstw/view'
    },
    'bundle': {
        'name': 'TTFD Bundle',
        'description': '🎁 Optimizer + Cleaner\n✅ Обе программы\n✅ Выгодная цена',
        'price': 30,  # Stars
        'download_url': 'both'
    }
}

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /shop - показать магазин"""
    telegram_id = str(update.effective_user.id)
    user = db.get_user(telegram_id)
    
    # Обновляем имя пользователя
    db.update_user(
        telegram_id,
        username=update.effective_user.username or 'Unknown',
        first_name=update.effective_user.first_name or ''
    )
    
    # Формируем сообщение магазина
    message = "🛍️ <b>TTFD Software Shop</b>\n\n"
    message += "Выбери программу для покупки:\n\n"
    
    # Кнопки для каждого продукта
    keyboard = []
    
    for product_id, product in PRODUCTS.items():
        message += f"<b>{product['name']}</b>\n"
        message += f"{product['description']}\n"
        message += f"💰 Цена: {product['price']} ⭐ Stars\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"Купить {product['name']} ({product['price']}⭐)",
                callback_data=f"shop_buy_{product_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("📦 Мои покупки", callback_data="shop_purchases")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def shop_buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик покупки продукта"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем product_id из callback_data
    product_id = query.data.replace("shop_buy_", "")
    
    if product_id not in PRODUCTS:
        await query.edit_message_text("❌ Продукт не найден")
        return
    
    product = PRODUCTS[product_id]
    telegram_id = str(update.effective_user.id)
    
    # Создаём invoice для Telegram Stars
    title = product['name']
    description = product['description']
    payload = f"shop_{product_id}_{telegram_id}_{secrets.token_hex(8)}"
    currency = "XTR"  # Telegram Stars
    prices = [LabeledPrice(label=product['name'], amount=product['price'])]
    
    try:
        # Отправляем invoice
        await context.bot.send_invoice(
            chat_id=update.effective_chat.id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # Пустой для Stars
            currency=currency,
            prices=prices
        )
        
        await query.edit_message_text(
            f"✅ Счёт создан!\n\n"
            f"Оплати {product['price']} ⭐ Stars чтобы получить {product['name']}"
        )
    except Exception as e:
        print(f"❌ Ошибка создания invoice: {e}")
        await query.edit_message_text(
            f"❌ Ошибка создания счёта\n\n"
            f"Попробуй позже или обратись к администратору"
        )

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pre-checkout callback - проверка перед оплатой"""
    query = update.pre_checkout_query
    
    # Всегда подтверждаем (можно добавить дополнительные проверки)
    await query.answer(ok=True)

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик успешной оплаты"""
    payment = update.message.successful_payment
    telegram_id = str(update.effective_user.id)
    
    # Парсим payload
    payload_parts = payment.invoice_payload.split("_")
    if len(payload_parts) < 3:
        await update.message.reply_text("❌ Ошибка обработки платежа")
        return
    
    product_id = payload_parts[1]
    
    if product_id not in PRODUCTS:
        await update.message.reply_text("❌ Продукт не найден")
        return
    
    product = PRODUCTS[product_id]
    
    # Генерируем токен для скачивания
    download_token = secrets.token_urlsafe(32)
    
    # Сохраняем покупку в БД
    purchase_data = {
        'product_id': product_id,
        'price_stars': product['price'],
        'payment_charge_id': payment.telegram_payment_charge_id,
        'download_token': download_token,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
    }
    
    db.save_purchase(telegram_id, purchase_data)
    
    # Формируем сообщение с ссылкой на скачивание
    message = f"✅ <b>Покупка успешна!</b>\n\n"
    message += f"Ты купил: <b>{product['name']}</b>\n"
    message += f"Оплачено: {product['price']} ⭐ Stars\n\n"
    
    if product['download_url'] == 'both':
        # Bundle - обе программы
        optimizer = PRODUCTS['optimizer']
        cleaner = PRODUCTS['cleaner']
        message += f"📥 <b>Ссылки на скачивание:</b>\n\n"
        message += f"🚀 TTFD Optimizer:\n{optimizer['download_url']}\n\n"
        message += f"🧹 TTFD Cleaner:\n{cleaner['download_url']}\n\n"
    else:
        message += f"📥 <b>Ссылка на скачивание:</b>\n{product['download_url']}\n\n"
    
    message += f"⏰ Ссылка действительна 7 дней\n"
    message += f"💬 Вопросы? Напиши @bxdsun"
    
    await update.message.reply_text(message, parse_mode='HTML')
    
    # Уведомляем админов
    admin_message = f"💰 <b>Новая покупка!</b>\n\n"
    admin_message += f"Пользователь: {update.effective_user.first_name} (@{update.effective_user.username})\n"
    admin_message += f"Продукт: {product['name']}\n"
    admin_message += f"Цена: {product['price']} ⭐ Stars"
    
    for admin_id in TELEGRAM_ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='HTML'
            )
        except:
            pass

async def shop_purchases_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать покупки пользователя"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(update.effective_user.id)
    purchases = db.get_user_purchases(telegram_id)
    
    if not purchases:
        await query.edit_message_text(
            "📦 <b>Твои покупки</b>\n\n"
            "У тебя пока нет покупок\n"
            "Используй /shop чтобы купить программы",
            parse_mode='HTML'
        )
        return
    
    message = "📦 <b>Твои покупки</b>\n\n"
    
    for purchase in purchases:
        product_id = purchase['product_id']
        if product_id in PRODUCTS:
            product = PRODUCTS[product_id]
            created_at = datetime.fromisoformat(purchase['created_at'])
            
            message += f"• <b>{product['name']}</b>\n"
            message += f"  Дата: {created_at.strftime('%d.%m.%Y %H:%M')}\n"
            message += f"  Цена: {purchase['price_stars']} ⭐ Stars\n\n"
    
    keyboard = [[
        InlineKeyboardButton("🛍️ Вернуться в магазин", callback_data="shop_menu")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def shop_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вернуться в меню магазина"""
    query = update.callback_query
    await query.answer()
    
    # Формируем сообщение магазина
    message = "🛍️ <b>TTFD Software Shop</b>\n\n"
    message += "Выбери программу для покупки:\n\n"
    
    # Кнопки для каждого продукта
    keyboard = []
    
    for product_id, product in PRODUCTS.items():
        message += f"<b>{product['name']}</b>\n"
        message += f"{product['description']}\n"
        message += f"💰 Цена: {product['price']} ⭐ Stars\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"Купить {product['name']} ({product['price']}⭐)",
                callback_data=f"shop_buy_{product_id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("📦 Мои покупки", callback_data="shop_purchases")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        parse_mode='HTML',
        reply_markup=reply_markup
    )
