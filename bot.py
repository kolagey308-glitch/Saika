import json
import logging
import base64
import os
import asyncio
from io import BytesIO
from datetime import datetime

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ (ТВОИ ДАННЫЕ) ---
BOT_TOKEN = "8451686285:AAFWffo20dsC1f3XSFpLKDtAQpZWmcgKJyM"
MAIN_ADMIN = 1471307057
SECOND_ADMIN = 7066870264
WEBAPP_URL = "https://saika-app-gamma.vercel.app"

SCREENSHOTS_DIR = "screenshots"
ORDERS_FILE = "orders_db.json"
FILES_FILE = "files_db.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# --- БАЗА ДАННЫХ ---
def load_orders():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def load_files_db():
    if os.path.exists(FILES_FILE):
        with open(FILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_files_db(files):
    with open(FILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(files, f, ensure_ascii=False, indent=2)

orders_db = load_orders()
files_db = load_files_db()
admin_state = {}
pending_orders = {}

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

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def emoji(id, char): 
    return f'<tg-emoji emoji-id="{id}">{char}</tg-emoji>'

def is_admin(user_id):
    return user_id in [MAIN_ADMIN, SECOND_ADMIN]

# --- КЛАВИАТУРЫ ---
def main_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "🛍️ Магазин", "callback_data": "shop_bot", "icon_custom_emoji_id": "5938413566624272793"},
                {"text": "👤 Профиль", "callback_data": "profile", "icon_custom_emoji_id": "5879770735999717115"}
            ],
            [
                {"text": "🌐 Web Магазин", "web_app": {"url": WEBAPP_URL}}
            ]
        ]
    }

def shop_categories():
    return {
        "inline_keyboard": [
            [{"text": "VPN ДЛЯ PUBG", "callback_data": "cat_vpn", "icon_custom_emoji_id": "5294298833071674944"}],
            [{"text": "МАГНИТ & ПАКИ", "callback_data": "cat_extra", "icon_custom_emoji_id": "5296606007898705683"}],
            [{"text": "DNS СЕРВИСЫ", "callback_data": "cat_dns", "icon_custom_emoji_id": "5330324013728158014"}],
            [{"text": "НАЗАД", "callback_data": "back_menu", "icon_custom_emoji_id": "5960671702059848143"}]
        ]
    }

def products_keyboard(category: str):
    keyboard = []
    for item in CATALOG[category]:
        old_price = f" ❗{item['old']}₽" if item['old'] else ""
        btn_text = f"{item['name']} | {item['price']}₽{old_price} | {item['stock']} шт."
        keyboard.append([{"text": btn_text, "callback_data": f"buy_{category}_{item['name']}"}])
    keyboard.append([{"text": "К КАТЕГОРИЯМ", "callback_data": "shop_bot", "icon_custom_emoji_id": "5960671702059848143"}])
    return {"inline_keyboard": keyboard}

def payment_keyboard(product: str, price: int):
    return {
        "inline_keyboard": [
            [{"text": "Я ОПЛАТИЛ, ОТПРАВИТЬ ЧЕК", "callback_data": f"paid_{product}_{price}", "icon_custom_emoji_id": "5294351875917779401"}],
            [{"text": "ВЫБРАТЬ ДРУГОЙ ТОВАР", "callback_data": "shop_bot", "icon_custom_emoji_id": "5960671702059848143"}]
        ]
    }

def admin_order_keyboard(order_id: str):
    return {
        "inline_keyboard": [
            [
                {"text": "ПОДТВЕРДИТЬ", "callback_data": f"confirm_{order_id}", "icon_custom_emoji_id": "5310076249404621168"},
                {"text": "ОТКЛОНИТЬ", "callback_data": f"decline_{order_id}", "icon_custom_emoji_id": "5310169226856644648"}
            ],
            [
                {"text": "ЗАГРУЗИТЬ ФАЙЛ", "callback_data": f"uploadfile_{order_id}", "icon_custom_emoji_id": "5465300082628763143"}
            ]
        ]
    }

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = f'''
{emoji("5217822164362739968", "👑")} <b>SAIKA PREMIUM STORE</b>

Привет! Ты находишься в @vpnsaika_bot

{emoji("6030445631921721471", "🔥")} Качественные впн и многое другое только у нас

{emoji("5938413566624272793", "🛒")} <b>Магазин</b> — выбор товаров
{emoji("5879770735999717115", "👤")} <b>Профиль</b> — твои данные

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
            text=f"{emoji('5217822164362739968', '👑')} <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите раздел:",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    
    elif data == "shop_bot":
        text = f"{emoji('5938413566624272793', '🛒')} <b>МАГАЗИН</b>\n\n{emoji('5350291836378307462', '📋')} Выберите категорию:"
        await query.edit_message_text(text=text, reply_markup=shop_categories(), parse_mode="HTML")
    
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        titles = {
            "vpn": f"{emoji('5294298833071674944', '🔒')} VPN ДЛЯ PUBG",
            "extra": f"{emoji('5296606007898705683', '📦')} МАГНИТ & ПАКИ",
            "dns": f"{emoji('5330324013728158014', '🌐')} DNS СЕРВИСЫ"
        }
        await query.edit_message_text(
            text=f'{emoji("5350291836378307462", "📋")} <b>{titles[category]}</b>\n\nВыберите товар:',
            reply_markup=products_keyboard(category),
            parse_mode="HTML"
        )
    
    elif data.startswith("buy_"):
        _, category, product = data.split("_", 2)
        item = next((x for x in CATALOG[category] if x['name'] == product), None)
        
        if item:
            old_text = f" ❗{item['old']}₽" if item['old'] else ""
            text = f"""
{emoji("5217822164362739968", "👑")} <b>ОФОРМЛЕНИЕ ЗАКАЗА</b>

Товар: <b>{product}</b>
Цена: <b>{item['price']}₽</b>{old_text}
В наличии: {item['stock']} шт.

━━━━━━━━━━━━━━━━━━
✍️ <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:</b>

{emoji("5357059622505052938", "😀")} Банк: <b>Т-Банк</b>
{emoji("5206607081334906820", "👛")} Карта: <code>2200 7021 4895 7363</code>
{emoji("5879770735999717115", "👤")} Получатель: <b>Саид К.</b>

━━━━━━━━━━━━━━━━━━
<i>После оплаты нажмите кнопку ниже и загрузите скриншот чека</i>
"""
            await query.edit_message_text(text=text, reply_markup=payment_keyboard(product, item['price']), parse_mode="HTML")
    
    elif data == "profile":
        profile_text = f"""
{emoji("5879770735999717115", "👤")} <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>

{emoji("5879770735999717115", "👤")} Имя: <b>{user.first_name} {user.last_name or ''}</b>
{emoji("5886505193180239900", "🆔")} ID: <code>{user.id}</code>
{emoji("5814247475141153332", "📱")} Username: @{user.username or 'не указан'}

{emoji("5890925363067886150", "⭐")} Статус: {emoji("5217822164362739968", "👑")} <b>Premium Client</b>

Для покупок откройте магазин 👇
"""
        await query.edit_message_text(text=profile_text, reply_markup=main_menu(), parse_mode="HTML")

# --- Web App Data ---
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = json.loads(update.effective_message.web_app_data.data)
    
    action = data.get('action')
    logger.info(f"WebApp data from {user.id}: action={action}")
    
    if action == 'new_order':
        order = data.get('order')
        order_id = f"{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        new_order = {
            "id": order_id,
            "userId": user.id,
            "username": user.username or user.first_name,
            "product": order['product'],
            "price": order['price'],
            "comment": order.get('comment', ''),
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        
        orders_db.append(new_order)
        save_orders(orders_db)
        
        admin_msg = f"""
<b>🛒 НОВЫЙ ЗАКАЗ #{user.id}</b>

Товар: <b>{order['product']}</b>
Сумма: <b>{order['price']} ₽</b>
Покупатель: @{user.username or user.first_name} (ID: <code>{user.id}</code>)
Комментарий: {order.get('comment', 'нет')}
"""
        
        if order.get('screenshot'):
            try:
                screenshot_data = order['screenshot'].split(',')[1] if ',' in order['screenshot'] else order['screenshot']
                image_data = base64.b64decode(screenshot_data)
                
                user_folder = os.path.join(SCREENSHOTS_DIR, str(user.id))
                os.makedirs(user_folder, exist_ok=True)
                filepath = os.path.join(user_folder, f"{order_id}.jpg")
                
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                for admin_id in [MAIN_ADMIN, SECOND_ADMIN]:
                    try:
                        await context.bot.send_photo(
                            chat_id=admin_id,
                            photo=BytesIO(image_data),
                            caption=admin_msg,
                            reply_markup=admin_order_keyboard(order_id),
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Ошибка отправки админу {admin_id}: {e}")
            except Exception as e:
                logger.error(f"Ошибка скриншота: {e}")
        
        await update.effective_message.reply_text(
            f"{emoji('5217822164362739968', '👑')} <b>ЗАКАЗ ПРИНЯТ!</b>\n\n"
            f"Товар: {order['product']}\n"
            f"Сумма: {order['price']} ₽\n"
            f"Статус: {emoji('5296289868240948222', '⏳')} ОЖИДАЕТ ПРОВЕРКИ\n\n"
            "✔️ Администратор проверит оплату и отправит файлы.",
            parse_mode="HTML"
        )
    
    elif action == 'get_orders':
        user_orders = [o for o in orders_db if o['userId'] == user.id]
        await update.effective_message.reply_text(
            json.dumps({"success": True, "orders": user_orders})
        )
    
    elif action == 'get_all_orders':
        if is_admin(user.id):
            await update.effective_message.reply_text(
                json.dumps({"success": True, "orders": orders_db})
            )
    
    elif action == 'get_files':
        if user.id == MAIN_ADMIN:
            await update.effective_message.reply_text(
                json.dumps({"success": True, "files": files_db})
            )

async def cleanup_webhook():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook deleted")

def main():
    asyncio.run(cleanup_webhook())
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!confirm_|decline_|uploadfile_).*"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    logger.info("🚀 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
