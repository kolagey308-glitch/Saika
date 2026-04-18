import json
import logging
import base64
import os
import asyncio
from io import BytesIO
from datetime import datetime
import requests

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8451686285:AAFWffo20dsC1f3XSFpLKDtAQpZWmcgKJyM"
MAIN_ADMIN = 1471307057
SECOND_ADMIN = 7066870264
WEBAPP_URL = "https://saika-app-gamma.vercel.app"

SCREENSHOTS_DIR = "screenshots"
ORDERS_FILE = "orders_db.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# --- АВТОВЫДАЧА ТОВАРОВ (ФАЙЛЫ) ---
PRODUCT_FILES = {
    "GTR VPN": {"url": "https://files.catbox.moe/cwy1n3.conf", "name": "GTR_VPN.conf"},
    "VIP VPN": {"url": "https://files.catbox.moe/ab8a1r.conf", "name": "VIP_VPN.conf"},
    "ULTRA MAX VPN": {"url": "https://files.catbox.moe/rqbq5r.conf", "name": "ULTRA_MAX.conf"},
    "STRONG VPN": {"url": "https://files.catbox.moe/e6a8yh.conf", "name": "STRONG_VPN.conf"},
    "SAIKA S1 VPN": {"url": "https://files.catbox.moe/1coq6u.conf", "name": "SAIKA_S1.conf"},
    "DEAD ALL VPN": {"url": "https://files.catbox.moe/ohvc5d.conf", "name": "DEAD_ALL.conf"},
    "TDM SKILL VPN": {"url": "https://files.catbox.moe/ohvc5d.conf", "name": "TDM_SKILL.conf"},
    "FUCK VPN": {"url": "https://files.catbox.moe/3ghk4a.conf", "name": "FUCK_VPN.conf"},
    "UNLY VPN": {"url": "https://files.catbox.moe/5qcb3b.conf", "name": "UNLY_VPN.conf"},
    "Магнит андроид": {"url": "https://files.catbox.moe/qahmjb.zip", "name": "Magnet_Android.zip"},
    "Магнит ios": {"url": "https://files.catbox.moe/ql2d0s.mobileconfig", "name": "DNS_iOS.mobileconfig"},
    "Пак unly": {"url": "https://files.catbox.moe/qahmjb.zip", "name": "Unly_Pack.zip"},
    "DNS android": {"url": "https://files.catbox.moe/ql2d0s.mobileconfig", "name": "DNS_Android.mobileconfig"},
    "DNS Ios": {"url": "https://files.catbox.moe/ql2d0s.mobileconfig", "name": "DNS_iOS.mobileconfig"},
    "Пак сайки": {"url": "https://www.icloud.com/shortcuts/83963f23bcc94e7a85bbbe0c6a56e350", "name": "Saika_Pack", "is_link": True}
}

# --- КАТАЛОГ ТОВАРОВ ---
CATALOG = {
    "vpn": [
        {"name": "SAIKA S1 VPN", "price": 79, "old": 1199, "stock": "9"},
        {"name": "VIP VPN", "price": 79, "old": 529, "stock": "10"},
        {"name": "GTR VPN", "price": 79, "old": 899, "stock": "∞"},
        {"name": "ULTRA MAX VPN", "price": 79, "old": 629, "stock": "8"},
        {"name": "STRONG VPN", "price": 79, "old": 499, "stock": "∞"},
        {"name": "UNLY VPN", "price": 79, "old": 399, "stock": "∞"},
        {"name": "TDM SKILL VPN", "price": 79, "old": 199, "stock": "∞"},
        {"name": "FUCK VPN", "price": 49, "old": 139, "stock": "∞"},
        {"name": "DEAD ALL VPN", "price": 79, "old": 1299, "stock": "∞"}
    ],
    "extra": [
        {"name": "Магнит андроид", "price": 169, "old": 259, "stock": "∞"},
        {"name": "Магнит ios", "price": 269, "old": None, "stock": "∞"},
        {"name": "Пак сайки", "price": 639, "old": 1789, "stock": "∞"},
        {"name": "Пак unly", "price": 79, "old": 1299, "stock": "10"}
    ],
    "dns": [
        {"name": "DNS android", "price": 129, "old": 239, "stock": "∞"},
        {"name": "DNS Ios", "price": 129, "old": 239, "stock": "∞"}
    ]
}

# --- БАЗА ДАННЫХ ---
def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

orders_db = load_orders()
user_orders = {}
pending_orders = {}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(user_id):
    return user_id in [MAIN_ADMIN, SECOND_ADMIN]

# --- КЛАВИАТУРЫ ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ Магазин", callback_data="shop_bot"),
         InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("🌐 Web Магазин", web_app={"url": WEBAPP_URL})]
    ])

def shop_categories():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔒 VPN ДЛЯ PUBG", callback_data="cat_vpn")],
        [InlineKeyboardButton("📦 МАГНИТ & ПАКИ", callback_data="cat_extra")],
        [InlineKeyboardButton("🌐 DNS СЕРВИСЫ", callback_data="cat_dns")],
        [InlineKeyboardButton("◀️ НАЗАД", callback_data="back_menu")]
    ])

def products_keyboard(category: str):
    keyboard = []
    for item in CATALOG[category]:
        old_price = f" ❗{item['old']}₽" if item['old'] else ""
        btn_text = f"{item['name']} | {item['price']}₽{old_price} | {item['stock']} шт."
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_{category}_{item['name']}")])
    keyboard.append([InlineKeyboardButton("◀️ К КАТЕГОРИЯМ", callback_data="shop_bot")])
    return InlineKeyboardMarkup(keyboard)

def payment_keyboard(product: str, price: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Я ОПЛАТИЛ, ОТПРАВИТЬ ЧЕК", callback_data=f"paid_{product}_{price}")],
        [InlineKeyboardButton("◀️ ВЫБРАТЬ ДРУГОЙ ТОВАР", callback_data="shop_bot")]
    ])

def admin_order_keyboard(order_id: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ПОДТВЕРДИТЬ", callback_data=f"confirm_{order_id}"),
         InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"decline_{order_id}")]
    ])

def download_keyboard(file_url: str, file_name: str):
    """Кнопка для скачивания файла"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📥 СКАЧАТЬ {file_name}", url=file_url)]
    ])

# --- АВТОВЫДАЧА С КНОПКОЙ СКАЧАТЬ ---
async def auto_send_product(bot, user_id, product_name):
    logger.info(f"🚀 Автовыдача для {user_id}: {product_name}")
    
    if product_name in PRODUCT_FILES:
        file_info = PRODUCT_FILES[product_name]
        
        if file_info.get("is_link"):
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ <b>ЗАКАЗ ГОТОВ!</b>\n\nТовар: <b>{product_name}</b>\n\nНажмите кнопку ниже чтобы скачать:",
                parse_mode="HTML",
                reply_markup=download_keyboard(file_info["url"], file_info["name"])
            )
        else:
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ <b>ЗАКАЗ ГОТОВ!</b>\n\nТовар: <b>{product_name}</b>\n\nНажмите кнопку ниже чтобы скачать файл:",
                parse_mode="HTML",
                reply_markup=download_keyboard(file_info["url"], file_info["name"])
            )
        
        await bot.send_message(
            chat_id=user_id,
            text="📝 <b>ОСТАВЬТЕ ОТЗЫВ</b> @saikamng\n\n💔 СЛИЛ ТОВАР\n😡 ИСПОРТИЛ ЕГО И ПОТЕРЯЛ ДЕНЬГИ",
            parse_mode="HTML"
        )
        return True
    
    logger.warning(f"⚠️ Товар {product_name} не найден")
    return False

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = '''
👑 <b>SAIKA PREMIUM STORE</b>

Привет! Ты находишься в @vpnsaika_bot

🔥 Качественные впн и многое другое только у нас

🛍️ <b>Магазин</b> — выбор товаров
👤 <b>Профиль</b> — твои данные

Выбери действие ниже:
'''
    await update.message.reply_text(text=welcome, reply_markup=main_menu(), parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    
    if data == "back_menu":
        await query.edit_message_text(
            text="👑 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите раздел:",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    
    elif data == "shop_bot":
        text = "🛍️ <b>МАГАЗИН</b>\n\n📋 Выберите категорию:"
        await query.edit_message_text(text=text, reply_markup=shop_categories(), parse_mode="HTML")
    
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        titles = {"vpn": "🔒 VPN ДЛЯ PUBG", "extra": "📦 МАГНИТ & ПАКИ", "dns": "🌐 DNS СЕРВИСЫ"}
        await query.edit_message_text(
            text=f'📋 <b>{titles[category]}</b>\n\nВыберите товар:',
            reply_markup=products_keyboard(category),
            parse_mode="HTML"
        )
    
    elif data.startswith("buy_"):
        _, category, product = data.split("_", 2)
        item = next((x for x in CATALOG[category] if x['name'] == product), None)
        
        if item:
            user_orders[user.id] = {"product": product, "price": item['price']}
            old_text = f" ❗{item['old']}₽" if item['old'] else ""
            text = f"""
👑 <b>ОФОРМЛЕНИЕ ЗАКАЗА</b>

Товар: <b>{product}</b>
Цена: <b>{item['price']}₽</b>{old_text}
В наличии: {item['stock']} шт.

━━━━━━━━━━━━━━━━━━
✍️ <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:</b>

😀 Банк: <b>Т-Банк</b>
👛 Карта: <code>2200 7021 4895 7363</code>
👤 Получатель: <b>Саид К.</b>

━━━━━━━━━━━━━━━━━━
<i>После оплаты нажмите кнопку ниже и загрузите скриншот чека</i>
"""
            await query.edit_message_text(text=text, reply_markup=payment_keyboard(product, item['price']), parse_mode="HTML")
    
    elif data.startswith("paid_"):
        _, product, price = data.split("_", 2)
        text = f"""
😀 <b>ЗАГРУЗИТЕ ЧЕК</b>

Товар: <b>{product}</b>
Сумма: <b>{price}₽</b>

📸 Отправьте скриншот оплаты <b>ПРЯМО В ЭТОТ ЧАТ</b>
💬 Можете добавить комментарий к фото

<i>Администратор проверит и отправит файлы</i>
"""
        await query.edit_message_text(
            text=text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ ОТМЕНА", callback_data="shop_bot")]])
        )
        user_orders[user.id] = {"product": product, "price": price, "awaiting": "photo"}
    
    elif data == "profile":
        profile_text = f"""
👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>

👤 Имя: <b>{user.first_name} {user.last_name or ''}</b>
🆔 ID: <code>{user.id}</code>
📱 Username: @{user.username or 'не указан'}

⭐ Статус: 👑 <b>Premium Client</b>

Для покупок откройте магазин 👇
"""
        await query.edit_message_text(text=profile_text, reply_markup=main_menu(), parse_mode="HTML")

# --- ОБРАБОТКА ФОТО ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    
    order = user_orders.get(user.id, {})
    product = order.get('product', 'Неизвестный товар')
    price = order.get('price', '?')
    
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    
    order_id = f"{user.id}_{product}_{price}".replace(" ", "_")
    pending_orders[order_id] = {"user_id": user.id, "product": product, "price": price}
    
    admin_msg = f"<b>🛒 НОВЫЙ ЗАКАЗ #{user.id}</b>\n\nТовар: <b>{product}</b>\nСумма: <b>{price} ₽</b>\n\nПокупатель: @{user.username or user.first_name} (ID: <code>{user.id}</code>)\nКомментарий: {caption or 'нет'}"
    
    for admin_id in [MAIN_ADMIN, SECOND_ADMIN]:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=BytesIO(photo_bytes),
                caption=admin_msg,
                reply_markup=admin_order_keyboard(order_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки админу {admin_id}: {e}")
    
    await update.message.reply_text(
        f"👑 <b>ЧЕК ПОЛУЧЕН!</b>\n\nТовар: <b>{product}</b>\nСумма: <b>{price} ₽</b>\nСтатус: ⏳ <b>ОЖИДАЕТ ПРОВЕРКИ</b>\n\n✔️ Администратор проверит оплату и отправит файлы.",
        parse_mode="HTML", reply_markup=main_menu()
    )
    
    if user.id in user_orders:
        del user_orders[user.id]

# --- ОБРАБОТКА КНОПОК АДМИНА ---
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    action = data_parts[0]
    order_id = "_".join(data_parts[1:])
    
    user = query.from_user
    
    if not is_admin(user.id):
        await query.answer("❌ Нет доступа")
        return
    
    if order_id not in pending_orders:
        await query.answer("❌ Заказ не найден")
        return
    
    order = pending_orders[order_id]
    user_id = order["user_id"]
    product = order["product"]
    price = order["price"]
    
    if action == "confirm":
        await context.bot.send_message(
            chat_id=user_id,
            text=f"✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\nТовар: <b>{product}</b>",
            parse_mode="HTML"
        )
        
        success = await auto_send_product(context.bot, user_id, product)
        
        if success:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ <b>ПОДТВЕРЖДЕНО И ОТПРАВЛЕНО</b>",
                parse_mode="HTML"
            )
        else:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ <b>ОШИБКА ОТПРАВКИ</b>",
                parse_mode="HTML"
            )
        
        del pending_orders[order_id]
    
    elif action == "decline":
        await context.bot.send_message(
            chat_id=user_id,
            text=f"❌ <b>ОПЛАТА НЕ ПОДТВЕРЖДЕНА</b>\n\nТовар: {product}\nСумма: {price} ₽",
            parse_mode="HTML"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML"
        )
        del pending_orders[order_id]

# --- WEB APP DATA ---
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = json.loads(update.effective_message.web_app_data.data)
    
    action = data.get('action')
    
    if action == 'new_order':
        order = data.get('order')
        order_id = f"{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        new_order = {
            "id": order_id, "userId": user.id, "username": user.username or user.first_name,
            "product": order['product'], "price": order['price'],
            "comment": order.get('comment', ''), "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        orders_db.append(new_order)
        save_orders(orders_db)
        
        pending_order_id = f"{user.id}_{order['product']}_{order['price']}".replace(" ", "_")
        pending_orders[pending_order_id] = {"user_id": user.id, "product": order['product'], "price": order['price']}
        
        admin_msg = f"<b>🛒 НОВЫЙ ЗАКАЗ (WEB) #{user.id}</b>\n\nТовар: <b>{order['product']}</b>\nСумма: <b>{order['price']} ₽</b>\nПокупатель: @{user.username or user.first_name} (ID: <code>{user.id}</code>)"
        
        if order.get('screenshot') and order['screenshot'].startswith('data:image'):
            try:
                screenshot_data = order['screenshot'].split(',')[1]
                image_data = base64.b64decode(screenshot_data)
                for admin_id in [MAIN_ADMIN, SECOND_ADMIN]:
                    await context.bot.send_photo(
                        chat_id=admin_id, photo=BytesIO(image_data),
                        caption=admin_msg, reply_markup=admin_order_keyboard(pending_order_id),
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.error(f"Ошибка скриншота: {e}")
        
        await update.effective_message.reply_text(
            f"👑 <b>ЗАКАЗ ПРИНЯТ!</b>\n\nТовар: {order['product']}\nСумма: {order['price']} ₽\nСтатус: ⏳ ОЖИДАЕТ",
            parse_mode="HTML"
        )

async def cleanup_webhook():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook deleted")

def main():
    asyncio.run(cleanup_webhook())
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!confirm_|decline_).*"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(confirm|decline)_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("🚀 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
