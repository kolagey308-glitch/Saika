import json
import logging
import base64
import os
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8507469444:AAGv0ZRhyazsuSdxkkr1eNRi3DTJdc127fw"
ADMIN_ID = 1471307057
WEBAPP_URL = "https://saika-app-gamma.vercel.app/"  # ЗАМЕНИ НА СВОЙ VERCEL URL

FILES_DB = "files_db.json"

def load_files():
    if os.path.exists(FILES_DB):
        with open(FILES_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_files(data):
    with open(FILES_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

product_files = load_files()
user_orders = {}
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

# TG Premium эмодзи ID
EMOJI = {
    "crown": "5217822164362739968",
    "fire": "6030445631921721471",
    "shop": "5938413566624272793",
    "profile": "5879770735999717115",
    "vpn": "5294298833071674944",
    "magnet": "5296606007898705683",
    "dns": "5330324013728158014",
    "back": "5960671702059848143",
    "clock": "5296289868240948222",
    "check": "5451732530048802485",
    "paid": "5294351875917779401",
    "cancel": "5294082710317338135",
    "bank": "5357059622505052938",
    "card": "5206607081334906820",
    "person": "5879770735999717115",
    "upload": "5465300082628763143",
    "success": "5310076249404621168",
    "danger": "5310169226856644648",
    "primary": "5285430309720966085"
}

def em(id): 
    return f'<tg-emoji emoji-id="{id}">👍</tg-emoji>'

# --- КЛАВИАТУРЫ СО СТИЛЯМИ ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{em(EMOJI['shop'])} Магазин", callback_data="shop_bot"),
         InlineKeyboardButton(f"{em(EMOJI['profile'])} Профиль", callback_data="profile")],
        [InlineKeyboardButton("🌐 Web Магазин", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])

def shop_categories():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{em(EMOJI['vpn'])} VPN ДЛЯ PUBG", callback_data="cat_vpn")],
        [InlineKeyboardButton(f"{em(EMOJI['magnet'])} МАГНИТ & ПАКИ", callback_data="cat_extra")],
        [InlineKeyboardButton(f"{em(EMOJI['dns'])} DNS СЕРВИСЫ", callback_data="cat_dns")],
        [InlineKeyboardButton(f"{em(EMOJI['back'])} НАЗАД", callback_data="back_menu")]
    ])

def products_keyboard(category: str):
    keyboard = []
    for item in CATALOG[category]:
        old_price = f" ❗{item['old']}₽" if item['old'] else ""
        btn_text = f"{item['name']} | {item['price']}₽{old_price} | {item['stock']} шт."
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"buy_{category}_{item['name']}")])
    keyboard.append([InlineKeyboardButton(f"{em(EMOJI['back'])} К КАТЕГОРИЯМ", callback_data="shop_bot")])
    return InlineKeyboardMarkup(keyboard)

def payment_keyboard(product: str, price: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{em(EMOJI['paid'])} Я ОПЛАТИЛ, ОТПРАВИТЬ ЧЕК", callback_data=f"paid_{product}_{price}")],
        [InlineKeyboardButton(f"{em(EMOJI['back'])} ВЫБРАТЬ ДРУГОЙ ТОВАР", callback_data="shop_bot")]
    ])

def admin_order_keyboard(order_id: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ПОДТВЕРДИТЬ", callback_data=f"confirm_{order_id}", icon_custom_emoji_id=EMOJI['success']),
         InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"decline_{order_id}", icon_custom_emoji_id=EMOJI['danger'])]
    ])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{em(EMOJI['upload'])} ЗАГРУЗИТЬ ФАЙЛЫ", callback_data="admin_upload_menu")],
        [InlineKeyboardButton("📋 СПИСОК ФАЙЛОВ", callback_data="admin_list_files")],
        [InlineKeyboardButton(f"{em(EMOJI['back'])} НАЗАД", callback_data="back_menu")]
    ])

def admin_upload_menu_keyboard():
    all_products = []
    for cat in CATALOG.values():
        for item in cat:
            all_products.append(item['name'])
    
    keyboard = []
    row = []
    for product in all_products:
        has_file = "✅" if product in product_files and product_files[product] else "📁"
        short_name = product[:14] + ".." if len(product) > 16 else product
        row.append(InlineKeyboardButton(f"{has_file} {short_name}", callback_data=f"admin_upload_{product}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(f"{em(EMOJI['back'])} В АДМИН-ПАНЕЛЬ", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = f'''
{em(EMOJI["crown"])} <b>SAIKA PREMIUM STORE</b>

Привет! Ты находишься в @vpnsaika_bot

{em(EMOJI["fire"])} Качественные впн и многое другое только у нас

{em(EMOJI["shop"])} <b>Магазин</b> — выбор товаров
{em(EMOJI["profile"])} <b>Профиль</b> — твои данные

Выбери действие ниже:
'''
    await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    
    # АДМИН-ПАНЕЛЬ
    if data == "admin_panel" and user.id == ADMIN_ID:
        text = f"{em(EMOJI['crown'])} <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите действие:"
        await query.edit_message_text(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")
    
    elif data == "admin_upload_menu" and user.id == ADMIN_ID:
        text = f"{em(EMOJI['upload'])} <b>ЗАГРУЗКА ФАЙЛОВ</b>\n\nВыберите товар:\n✅ - файлы загружены\n📁 - файлов нет"
        await query.edit_message_text(text, reply_markup=admin_upload_menu_keyboard(), parse_mode="HTML")
    
    elif data == "admin_list_files" and user.id == ADMIN_ID:
        text = "<b>📋 ТОВАРЫ С ФАЙЛАМИ:</b>\n\n"
        has_files = False
        for product, files in product_files.items():
            if files:
                has_files = True
                text += f"✅ <b>{product}</b>: {len(files)} файл(ов)\n"
        if not has_files:
            text += "❌ Нет загруженных файлов"
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{em(EMOJI['back'])} НАЗАД", callback_data="admin_panel")]
        ]))
    
    elif data.startswith("admin_upload_") and user.id == ADMIN_ID:
        product = data.replace("admin_upload_", "")
        admin_state[user.id] = {"action": "upload", "product": product}
        current_files = len(product_files.get(product, []))
        text = f"""
{em(EMOJI['upload'])} <b>ЗАГРУЗКА ФАЙЛА</b>

Товар: <b>{product}</b>

Отправьте файл (фото или документ) в этот чат.
Текущие файлы: {current_files} шт.
"""
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ ОЧИСТИТЬ ФАЙЛЫ", callback_data=f"admin_clear_{product}")],
            [InlineKeyboardButton(f"{em(EMOJI['back'])} НАЗАД", callback_data="admin_upload_menu")]
        ]))
    
    elif data.startswith("admin_clear_") and user.id == ADMIN_ID:
        product = data.replace("admin_clear_", "")
        if product in product_files:
            del product_files[product]
            save_files(product_files)
        await query.answer("✅ Файлы удалены")
        await query.edit_message_text(
            f"✅ Файлы для <b>{product}</b> удалены",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{em(EMOJI['back'])} НАЗАД", callback_data="admin_upload_menu")]])
        )
    
    # ОБЫЧНОЕ МЕНЮ
    elif data == "back_menu":
        await query.edit_message_text(
            f"{em(EMOJI['crown'])} <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите раздел:",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    
    elif data == "shop_bot":
        text = f"{em(EMOJI['shop'])} <b>МАГАЗИН</b>\n\nВыберите категорию:"
        await query.edit_message_text(text, reply_markup=shop_categories(), parse_mode="HTML")
    
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        titles = {
            "vpn": f"{em(EMOJI['vpn'])} VPN ДЛЯ PUBG", 
            "extra": f"{em(EMOJI['magnet'])} МАГНИТ & ПАКИ", 
            "dns": f"{em(EMOJI['dns'])} DNS СЕРВИСЫ"
        }
        await query.edit_message_text(
            f'<b>{titles[category]}</b>\n\nВыберите товар:',
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
{em(EMOJI['crown'])} <b>ОФОРМЛЕНИЕ ЗАКАЗА</b>

Товар: <b>{product}</b>
Цена: <b>{item['price']}₽</b>{old_text}
В наличии: {item['stock']} шт.

━━━━━━━━━━━━━━━━━━
✍️ <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:</b>

{em(EMOJI['bank'])} Банк: <b>Т-Банк</b>
{em(EMOJI['card'])} Карта: <code>2200 7021 4895 7363</code>
{em(EMOJI['person'])} Получатель: <b>Саид К.</b>

━━━━━━━━━━━━━━━━━━
<i>После оплаты нажмите кнопку ниже и загрузите скриншот чека</i>
"""
            await query.edit_message_text(text, reply_markup=payment_keyboard(product, item['price']), parse_mode="HTML")
    
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
            text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{em(EMOJI['back'])} ОТМЕНА", callback_data="shop_bot")]])
        )
        user_orders[user.id] = {"product": product, "price": price, "awaiting": "photo"}
    
    elif data == "profile":
        profile_text = f"""
{em(EMOJI['profile'])} <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>

{em(EMOJI['person'])} Имя: <b>{user.first_name} {user.last_name or ''}</b>
🆔 ID: <code>{user.id}</code>
📱 Username: @{user.username or 'не указан'}

⭐ Статус: {em(EMOJI['crown'])} <b>Premium Client</b>

Для покупок откройте магазин 👇
"""
        await query.edit_message_text(profile_text, reply_markup=main_menu(), parse_mode="HTML")

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    
    # Админ загружает файл
    if user.id == ADMIN_ID and user.id in admin_state and admin_state[user.id].get("action") == "upload":
        product = admin_state[user.id]["product"]
        
        if product not in product_files:
            product_files[product] = []
        
        file_info = {
            "file_id": photo.file_id,
            "file_name": f"photo_{len(product_files[product])}.jpg",
            "type": "photo"
        }
        product_files[product].append(file_info)
        save_files(product_files)
        
        await update.message.reply_text(f"✅ Фото добавлено к товару <b>{product}</b>\nВсего файлов: {len(product_files[product])}", parse_mode="HTML")
        return
    
    # Чек от пользователя
    order = user_orders.get(user.id, {})
    product = order.get('product', 'Неизвестный товар')
    price = order.get('price', '?')
    
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    
    order_id = f"{user.id}_{product}_{price}".replace(" ", "_")
    pending_orders[order_id] = {"user_id": user.id, "product": product, "price": price}
    
    admin_msg = f"<b>🛒 НОВЫЙ ЗАКАЗ #{user.id}</b>\n\nТовар: <b>{product}</b>\nСумма: <b>{price} ₽</b>\n\nПокупатель: @{user.username or user.first_name} (ID: <code>{user.id}</code>)\nКомментарий: {caption or 'нет'}"
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=BytesIO(photo_bytes),
        caption=admin_msg,
        reply_markup=admin_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    text = f"""
{em(EMOJI['crown'])} <b>ЧЕК ПОЛУЧЕН!</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>
Статус: {em(EMOJI['clock'])} <b>ОЖИДАЕТ ПРОВЕРКИ</b>

✔️ Администратор проверит оплату и отправит файлы в этот чат.
✨ Обычно это занимает 5-15 минут.
"""
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=main_menu())
    
    if user.id in user_orders:
        del user_orders[user.id]

# Обработка документов
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id == ADMIN_ID and user.id in admin_state and admin_state[user.id].get("action") == "upload":
        product = admin_state[user.id]["product"]
        doc = update.message.document
        
        if product not in product_files:
            product_files[product] = []
        
        file_info = {
            "file_id": doc.file_id,
            "file_name": doc.file_name,
            "type": "document"
        }
        product_files[product].append(file_info)
        save_files(product_files)
        
        await update.message.reply_text(f"✅ Файл <b>{doc.file_name}</b> добавлен к товару <b>{product}</b>\nВсего файлов: {len(product_files[product])}", parse_mode="HTML")

# Обработка кнопок админа
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    action = data_parts[0]
    order_id = "_".join(data_parts[1:])
    
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
            text=f"{em(EMOJI['crown'])} <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\nТовар: <b>{product}</b>\nСтатус: ✅ <b>УСПЕШНО</b>\n\nСейчас отправим файлы 👇",
            parse_mode="HTML"
        )
        
        files_sent = 0
        if product in product_files and product_files[product]:
            for file_info in product_files[product]:
                try:
                    if file_info["type"] == "document":
                        await context.bot.send_document(chat_id=user_id, document=file_info["file_id"])
                    else:
                        await context.bot.send_photo(chat_id=user_id, photo=file_info["file_id"])
                    files_sent += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки: {e}")
        
        await query.edit_message_caption(caption=query.message.caption + f"\n\n✅ <b>ПОДТВЕРЖДЕНО</b>", parse_mode="HTML")
        del pending_orders[order_id]
    
    elif action == "decline":
        await context.bot.send_message(chat_id=user_id, text=f"{em(EMOJI['cancel'])} <b>ОПЛАТА НЕ ПОДТВЕРЖДЕНА</b>\n\nПроверьте реквизиты.", parse_mode="HTML")
        await query.edit_message_caption(caption=query.message.caption + f"\n\n{em(EMOJI['cancel'])} <b>ОТКЛОНЕНО</b>", parse_mode="HTML")
        del pending_orders[order_id]

# Web App data
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = json.loads(update.effective_message.web_app_data.data)
    
    product = data.get('product')
    price = data.get('price')
    comment = data.get('comment', '')
    screenshot = data.get('screenshot')
    
    order_id = f"{user.id}_{product}_{price}".replace(" ", "_")
    pending_orders[order_id] = {"user_id": user.id, "product": product, "price": price}
    
    admin_msg = f"<b>🛒 ЗАКАЗ (WEB)</b>\n\nТовар: {product}\nСумма: {price}₽\nОт: @{user.username} ({user.id})\nКомментарий: {comment}"
    
    if screenshot and screenshot.startswith('data:image'):
        image_data = base64.b64decode(screenshot.split(',')[1])
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=BytesIO(image_data), caption=admin_msg, reply_markup=admin_order_keyboard(order_id), parse_mode="HTML")
    
    await update.effective_message.reply_text(f"{em(EMOJI['crown'])} <b>ЗАКАЗ ПРИНЯТ!</b>\n\nТовар: {product}\nСумма: {price}₽\nСтатус: {em(EMOJI['clock'])} ОЖИДАЕТ", parse_mode="HTML")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"{em(EMOJI['crown'])} <b>АДМИН-ПАНЕЛЬ</b>", reply_markup=admin_panel_keyboard(), parse_mode="HTML")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!confirm_|decline_).*"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(confirm|decline)_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("🚀 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    os.makedirs("files", exist_ok=True)
    main()
