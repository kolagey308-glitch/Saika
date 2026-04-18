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
WEBAPP_URL = "https://saika-store.vercel.app"  # ЗАМЕНИ НА СВОЙ VERCEL URL

# Хранилище файлов
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

# Каталог товаров
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

# --- КЛАВИАТУРЫ (БЕЗ СЛОЖНЫХ ЭМОДЗИ) ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ Магазин", callback_data="shop_bot"),
         InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton("🌐 Web Магазин", web_app=WebAppInfo(url=WEBAPP_URL))]
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

def admin_order_keyboard(user_id: int, product: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ПОДТВЕРДИТЬ", callback_data=f"confirm_{user_id}_{product}"),
         InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"decline_{user_id}")],
        [InlineKeyboardButton("📁 ЗАГРУЗИТЬ ФАЙЛ", callback_data=f"uploadfile_{product}")]
    ])

def admin_panel_keyboard():
    all_products = []
    for cat in CATALOG.values():
        for item in cat:
            all_products.append(item['name'])
    
    keyboard = []
    row = []
    for product in all_products:
        has_file = "✅" if product in product_files and product_files[product] else "📁"
        row.append(InlineKeyboardButton(f"{has_file} {product[:15]}", callback_data=f"admin_upload_{product}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 ОБНОВИТЬ", callback_data="admin_panel")])
    return InlineKeyboardMarkup(keyboard)

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"START from {update.effective_user.id}")
    welcome = """
👑 <b>SAIKA PREMIUM STORE</b>

Привет! Ты находишься в @vpnsaika_bot

🔥 Качественные впн и многое другое только у нас

🛍️ <b>Магазин</b> — выбор товаров
👤 <b>Профиль</b> — твои данные

Выбери действие ниже:
"""
    await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    
    logger.info(f"Button: {data} from {user.id}")
    
    # АДМИН-ПАНЕЛЬ
    if data == "admin_panel" and user.id == ADMIN_ID:
        text = "👑 <b>АДМИН-ПАНЕЛЬ</b>\n\nВыберите товар для загрузки файла:\n✅ - файл загружен\n📁 - файл отсутствует"
        await query.edit_message_text(text, reply_markup=admin_panel_keyboard(), parse_mode="HTML")
    
    elif data.startswith("admin_upload_") and user.id == ADMIN_ID:
        product = data.replace("admin_upload_", "")
        admin_state[user.id] = {"action": "upload", "product": product}
        text = f"""
📁 <b>ЗАГРУЗКА ФАЙЛА</b>

Товар: <b>{product}</b>

Отправьте файл в этот чат.
Текущие файлы: {len(product_files.get(product, []))} шт.
"""
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ ОЧИСТИТЬ ФАЙЛЫ", callback_data=f"admin_clear_{product}")],
            [InlineKeyboardButton("◀️ НАЗАД", callback_data="admin_panel")]
        ]))
    
    elif data.startswith("admin_clear_") and user.id == ADMIN_ID:
        product = data.replace("admin_clear_", "")
        if product in product_files:
            del product_files[product]
            save_files(product_files)
        await query.answer(f"Файлы для {product} удалены")
        await query.edit_message_text(
            f"✅ Файлы для {product} удалены",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ НАЗАД", callback_data="admin_panel")]])
        )
    
    # ОБЫЧНОЕ МЕНЮ
    elif data == "back_menu":
        await query.edit_message_text(
            "👑 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите раздел:",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    
    elif data == "shop_bot":
        text = '🛍️ <b>МАГАЗИН</b>\n\n📋 Выберите категорию:'
        await query.edit_message_text(text, reply_markup=shop_categories(), parse_mode="HTML")
    
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        titles = {"vpn": "🔒 VPN ДЛЯ PUBG", "extra": "📦 МАГНИТ & ПАКИ", "dns": "🌐 DNS СЕРВИСЫ"}
        await query.edit_message_text(
            f'📋 <b>{titles[category]}</b>\n\nВыберите товар:',
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
💳 Карта: <code>2200 7021 4895 7363</code>
👤 Получатель: <b>Саид К.</b>

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
        await query.edit_message_text(profile_text, reply_markup=main_menu(), parse_mode="HTML")

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    
    logger.info(f"Photo from {user.id}")
    
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
        
        await update.message.reply_text(
            f"✅ Фото добавлено к товару <b>{product}</b>\nВсего файлов: {len(product_files[product])}",
            parse_mode="HTML"
        )
        return
    
    # Чек от пользователя
    order = user_orders.get(user.id, {})
    product = order.get('product', 'Неизвестный товар')
    price = order.get('price', '?')
    
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    
    admin_msg = f"""
<b>🛒 НОВЫЙ ЗАКАЗ #{user.id}</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>

Покупатель: @{user.username or user.first_name} (ID: <code>{user.id}</code>)
Комментарий: {caption or 'нет'}
"""
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=BytesIO(photo_bytes),
        caption=admin_msg,
        reply_markup=admin_order_keyboard(user.id, product),
        parse_mode="HTML"
    )
    
    text = f"""
👑 <b>ЧЕК ПОЛУЧЕН!</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>
Статус: ⏳ <b>ОЖИДАЕТ ПРОВЕРКИ</b>

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
        
        await update.message.reply_text(
            f"✅ Файл <b>{doc.file_name}</b> добавлен к товару <b>{product}</b>\nВсего файлов: {len(product_files[product])}",
            parse_mode="HTML"
        )

# Обработка кнопок админа
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[0]
    
    if action == "confirm":
        user_id = int(data[1])
        product = "_".join(data[2:])
        
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
👑 <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>

Товар: <b>{product}</b>
Статус: ✅ <b>УСПЕШНО</b>

Сейчас отправим файлы 👇
""", parse_mode="HTML"
        )
        
        files_sent = 0
        if product in product_files:
            for file_info in product_files[product]:
                try:
                    if file_info["type"] == "document":
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=file_info["file_id"],
                            caption=f"📁 {file_info['file_name']}" if files_sent == 0 else ""
                        )
                    else:
                        await context.bot.send_photo(
                            chat_id=user_id,
                            photo=file_info["file_id"],
                            caption=f"🖼️ Файл для {product}" if files_sent == 0 else ""
                        )
                    files_sent += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки: {e}")
        
        if files_sent == 0:
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Файлы не загружены. Администратор отправит их вручную."
            )
        
        review_text = """
📝 <b>ОСТАВЬТЕ ОТЗЫВ ПОСЛЕ ПОЛУЧЕНИЯ</b> @saikamng

💔 СЛИЛ ТОВАР
😡 ИСПОРТИЛ ЕГО И ПОТЕРЯЛ ДЕНЬГИ
"""
        await context.bot.send_message(chat_id=user_id, text=review_text, parse_mode="HTML")
        
        await query.edit_message_caption(
            caption=query.message.caption + f"\n\n✅ <b>ПОДТВЕРЖДЕНО</b>\nФайлов: {files_sent}",
            parse_mode="HTML"
        )
    
    elif action == "decline":
        user_id = int(data[1])
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ <b>ОПЛАТА НЕ ПОДТВЕРЖДЕНА</b>\n\nПроверьте реквизиты или свяжитесь с @saikasupport",
            parse_mode="HTML"
        )
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML"
        )

# Web App data
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = json.loads(update.effective_message.web_app_data.data)
    
    product = data.get('product')
    price = data.get('price')
    comment = data.get('comment', '')
    screenshot = data.get('screenshot')
    
    admin_msg = f"<b>🛒 ЗАКАЗ (WEB)</b>\n\nТовар: {product}\nСумма: {price}₽\nОт: @{user.username} ({user.id})"
    
    if screenshot and screenshot.startswith('data:image'):
        image_data = base64.b64decode(screenshot.split(',')[1])
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=BytesIO(image_data),
            caption=admin_msg,
            reply_mup=admin_order_keyboard(user.id, product),
            parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_msg,
            reply_markup=admin_order_keyboard(user.id, product),
            parse_mode="HTML"
        )
    
    await update.effective_message.reply_text(
        f"👑 <b>ЗАКАЗ ПРИНЯТ!</b>\n\nТовар: {product}\nСумма: {price}₽\nСтатус: ⏳ ОЖИДАЕТ",
        parse_mode="HTML"
    )

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "👑 <b>АДМИН-ПАНЕЛЬ</b>",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML"
    )

def main():
    print("=== BOT STARTING ===", flush=True)
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(confirm|decline)_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    print("=== BOT RUNNING ===", flush=True)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    os.makedirs("files", exist_ok=True)
    main()
