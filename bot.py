import json
import logging
import base64
import os
import asyncio
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8507469444:AAGv0ZRhyazsuSdxkkr1eNRi3DTJdc127fw"
ADMIN_ID = 1471307057
WEBAPP_URL = "https://saika-store.vercel.app"

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

def emoji(id): 
    return f'<tg-emoji emoji-id="{id}">👍</tg-emoji>'

# --- КЛАВИАТУРЫ СТРОГО ПО ФОРМАТУ ---
def main_menu():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text=f"{emoji('5938413566624272793')} Магазин",
                callback_data="shop_bot"
            ),
            InlineKeyboardButton(
                text=f"{emoji('5879770735999717115')} Профиль",
                callback_data="profile"
            )
        ],
        [
            InlineKeyboardButton(
                text="🌐 Web Магазин",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ])

def shop_categories():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=f"{emoji('5294298833071674944')} VPN ДЛЯ PUBG",
            callback_data="cat_vpn"
        )],
        [InlineKeyboardButton(
            text=f"{emoji('5296606007898705683')} МАГНИТ & ПАКИ",
            callback_data="cat_extra"
        )],
        [InlineKeyboardButton(
            text=f"{emoji('5330324013728158014')} DNS СЕРВИСЫ",
            callback_data="cat_dns"
        )],
        [InlineKeyboardButton(
            text=f"{emoji('5960671702059848143')} НАЗАД",
            callback_data="back_menu"
        )]
    ])

def products_keyboard(category: str):
    keyboard = []
    for item in CATALOG[category]:
        old_price = f" ❗{item['old']}₽" if item['old'] else ""
        btn_text = f"{item['name']} | {item['price']}₽{old_price} | {item['stock']} шт."
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_{category}_{item['name']}")])
    keyboard.append([InlineKeyboardButton(
        text=f"{emoji('5960671702059848143')} К КАТЕГОРИЯМ",
        callback_data="shop_bot"
    )])
    return InlineKeyboardMarkup(keyboard)

def payment_keyboard(product: str, price: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=f"{emoji('5294351875917779401')} Я ОПЛАТИЛ, ОТПРАВИТЬ ЧЕК",
            callback_data=f"paid_{product}_{price}"
        )],
        [InlineKeyboardButton(
            text=f"{emoji('5960671702059848143')} ВЫБРАТЬ ДРУГОЙ ТОВАР",
            callback_data="shop_bot"
        )]
    ])

def admin_order_keyboard(order_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                text="✅ ПОДТВЕРДИТЬ",
                callback_data=f"confirm_{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ ОТКЛОНИТЬ",
                callback_data=f"decline_{order_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📁 ЗАГРУЗИТЬ ФАЙЛ ДЛЯ ЗАКАЗА",
                callback_data=f"uploadfile_{order_id}"
            )
        ]
    ])

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = f'''
{emoji("5217822164362739968")} <b>SAIKA PREMIUM STORE</b>

Привет! Ты находишься в @vpnsaika_bot

{emoji("6030445631921721471")} Качественные впн и многое другое только у нас

{emoji("5938413566624272793")} <b>Магазин</b> — выбор товаров
{emoji("5879770735999717115")} <b>Профиль</b> — твои данные

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
            text=f"{emoji('5217822164362739968')} <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите раздел:",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    
    elif data == "shop_bot":
        text = f"{emoji('5938413566624272793')} <b>МАГАЗИН</b>\n\n{emoji('5350291836378307462')} Выберите категорию:"
        await query.edit_message_text(text=text, reply_markup=shop_categories(), parse_mode="HTML")
    
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        titles = {
            "vpn": f"{emoji('5294298833071674944')} VPN ДЛЯ PUBG",
            "extra": f"{emoji('5296606007898705683')} МАГНИТ & ПАКИ",
            "dns": f"{emoji('5330324013728158014')} DNS СЕРВИСЫ"
        }
        await query.edit_message_text(
            text=f'{emoji("5350291836378307462")} <b>{titles[category]}</b>\n\nВыберите товар:',
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
{emoji("5217822164362739968")} <b>ОФОРМЛЕНИЕ ЗАКАЗА</b>

Товар: <b>{product}</b>
Цена: <b>{item['price']}₽</b>{old_text}
В наличии: {item['stock']} шт.

━━━━━━━━━━━━━━━━━━
✍️ <b>РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:</b>

{emoji("5357059622505052938")} Банк: <b>Т-Банк</b>
{emoji("5206607081334906820")} Карта: <code>2200 7021 4895 7363</code>
{emoji("5879770735999717115")} Получатель: <b>Саид К.</b>

━━━━━━━━━━━━━━━━━━
<i>После оплаты нажмите кнопку ниже и загрузите скриншот чека</i>

{emoji("5197269100878907942")} {emoji("5357059622505052938")} {emoji("5769126056262898415")} {emoji("5208893150692661284")}
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

{emoji("5296289868240948222")} {emoji("5258205968025525531")} {emoji("5465300082628763143")}
"""
        await query.edit_message_text(
            text=text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text=f"{emoji('5960671702059848143')} ОТМЕНА", callback_data="shop_bot")]])
        )
        user_orders[user.id] = {"product": product, "price": price, "awaiting": "photo"}
    
    elif data == "profile":
        profile_text = f"""
{emoji("5879770735999717115")} <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>

{emoji("5879770735999717115")} Имя: <b>{user.first_name} {user.last_name or ''}</b>
{emoji("5886505193180239900")} ID: <code>{user.id}</code>
{emoji("5814247475141153332")} Username: @{user.username or 'не указан'}

{emoji("5890925363067886150")} Статус: {emoji("5217822164362739968")} <b>Premium Client</b>

Для покупок откройте магазин 👇
"""
        await query.edit_message_text(text=profile_text, reply_markup=main_menu(), parse_mode="HTML")

# Обработка фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    
    # Админ загружает файл для заказа
    if user.id == ADMIN_ID and user.id in admin_state:
        state = admin_state[user.id]
        if state.get("action") == "upload_for_order":
            order_id = state.get("order_id")
            if order_id in pending_orders:
                order = pending_orders[order_id]
                user_id = order["user_id"]
                product = order["product"]
                
                # Сначала описание
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"{emoji('5217822164362739968')} <b>ЗАКАЗ ГОТОВ!</b>\n\nТовар: <b>{product}</b>\n\nСпасибо за покупку!",
                    parse_mode="HTML"
                )
                # Потом файл
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=photo.file_id,
                    caption=f"📁 Файл для {product}"
                )
                
                await update.message.reply_text(f"✅ Файл отправлен пользователю {user_id}")
                del admin_state[user.id]
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
    
    sent_msg = await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=BytesIO(photo_bytes),
        caption=admin_msg,
        reply_markup=admin_order_keyboard(order_id),
        parse_mode="HTML"
    )
    
    pending_orders[order_id]["admin_msg_id"] = sent_msg.message_id
    pending_orders[order_id]["original_caption"] = admin_msg
    
    text = f"""
{emoji("5217822164362739968")} <b>ЧЕК ПОЛУЧЕН!</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>
Статус: {emoji("5296289868240948222")} <b>ОЖИДАЕТ ПРОВЕРКИ</b>

✔️ Администратор проверит оплату и отправит файлы в этот чат.
✨ Обычно это занимает 5-15 минут.

{emoji("5296289868240948222")} {emoji("5451732530048802485")} {emoji("5294351875917779401")} {emoji("5294082710317338135")}
"""
    await update.message.reply_text(text=text, parse_mode="HTML", reply_markup=main_menu())
    
    if user.id in user_orders:
        del user_orders[user.id]

# Обработка кнопок админа
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_parts = query.data.split("_")
    action = data_parts[0]
    order_id = "_".join(data_parts[1:])
    
    if action == "uploadfile":
        if order_id in pending_orders:
            admin_state[query.from_user.id] = {"action": "upload_for_order", "order_id": order_id}
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n📁 <b>Отправьте файл для этого заказа (фото или документ)</b>",
                parse_mode="HTML"
            )
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
            text=f"""
{emoji("5217822164362739968")} <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>

Товар: <b>{product}</b>
Статус: ✅ <b>УСПЕШНО</b>

Администратор сейчас отправит файлы 👇
""",
            parse_mode="HTML"
        )
        
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n✅ <b>ПОДТВЕРЖДЕНО</b>\nНажмите \"ЗАГРУЗИТЬ ФАЙЛ\" чтобы отправить файл пользователю",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="📁 ЗАГРУЗИТЬ ФАЙЛ",
                    callback_data=f"uploadfile_{order_id}"
                )
            ]])
        )
        
        review_text = f"""
{emoji("5440539497383087970")} <b>ОСТАВЬТЕ ОТЗЫВ ПОСЛЕ ПОЛУЧЕНИЯ</b> @saikamng

{emoji("5314504236132747481")} СЛИЛ ТОВАР
{emoji("5206607081334906820")} ИСПОРТИЛ ЕГО И ПОТЕРЯЛ ДЕНЬГИ
"""
        await context.bot.send_message(chat_id=user_id, text=review_text, parse_mode="HTML")
    
    elif action == "decline":
        await context.bot.send_message(
            chat_id=user_id,
            text=f"""
{emoji("5294082710317338135")} <b>ОПЛАТА НЕ ПОДТВЕРЖДЕНА</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>

Проверьте реквизиты или свяжитесь с @saikasupport
""",
            parse_mode="HTML"
        )
        
        await query.edit_message_caption(
            caption=query.message.caption + f"\n\n{emoji('5294082710317338135')} <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML"
        )
        
        del pending_orders[order_id]

# Обработка документов
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document
    
    if user.id == ADMIN_ID and user.id in admin_state:
        state = admin_state[user.id]
        if state.get("action") == "upload_for_order":
            order_id = state.get("order_id")
            if order_id in pending_orders:
                order = pending_orders[order_id]
                user_id = order["user_id"]
                product = order["product"]
                
                # Сначала описание
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"{emoji('5217822164362739968')} <b>ЗАКАЗ ГОТОВ!</b>\n\nТовар: <b>{product}</b>\n\nСпасибо за покупку!",
                    parse_mode="HTML"
                )
                # Потом файл
                await context.bot.send_document(
                    chat_id=user_id,
                    document=doc.file_id,
                    caption=f"📁 {doc.file_name}"
                )
                
                await update.message.reply_text(f"✅ Файл отправлен пользователю {user_id}")
                del admin_state[user.id]

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
        sent_msg = await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=BytesIO(image_data),
            caption=admin_msg,
            reply_markup=admin_order_keyboard(order_id),
            parse_mode="HTML"
        )
        pending_orders[order_id]["admin_msg_id"] = sent_msg.message_id
        pending_orders[order_id]["original_caption"] = admin_msg
    
    await update.effective_message.reply_text(
        text=f"{emoji('5217822164362739968')} <b>ЗАКАЗ ПРИНЯТ!</b>\n\nТовар: {product}\nСумма: {price}₽\nСтатус: {emoji('5296289868240948222')} ОЖИДАЕТ",
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
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(?!confirm_|decline_|uploadfile_).*"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(confirm|decline|uploadfile)_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("🚀 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    os.makedirs("files", exist_ok=True)
    main()
