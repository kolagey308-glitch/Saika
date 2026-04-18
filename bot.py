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
WEBAPP_URL = "https://saika-production.up.railway.app"  # Твой Railway домен

# Каталог товаров
CATALOG = {
    "vpn": [
        {"name": "SAIKA S1 VPN", "price": 79, "old": 1199, "stock": 9},
        {"name": "VIP VPN", "price": 79, "old": 529, "stock": 10},
        {"name": "GTR VPN", "price": 79, "old": 899, "stock": "∞"},
        {"name": "ULTRA MAX VPN", "price": 79, "old": 629, "stock": 8},
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
        {"name": "Пак unly", "price": 79, "old": 1299, "stock": 10}
    ],
    "dns": [
        {"name": "DNS android", "price": 129, "old": 239, "stock": "∞"},
        {"name": "DNS Ios", "price": 129, "old": 239, "stock": "∞"}
    ]
}

# База файлов для товаров
PRODUCT_FILES = {
    "SAIKA S1 VPN": ["files/saika_s1.ovpn", "files/saika_s1.conf"],
    "VIP VPN": ["files/vip.ovpn"],
    "GTR VPN": ["files/gtr.ovpn"],
    "ULTRA MAX VPN": ["files/ultra.ovpn"],
    "STRONG VPN": ["files/strong.ovpn"],
    "UNLY VPN": ["files/unly.ovpn"],
    "TDM SKILL VPN": ["files/tdm.ovpn"],
    "FUCK VPN": ["files/fuck.ovpn"],
    "DEAD ALL VPN": ["files/dead.ovpn"],
    "Магнит андроид": ["files/magnet.apk"],
    "Магнит ios": ["files/magnet.ipa"],
    "Пак сайки": ["files/saika_pack.zip"],
    "Пак unly": ["files/unly_pack.zip"],
    "DNS android": ["files/dns_android.txt"],
    "DNS Ios": ["files/dns_ios.txt"]
}

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Временное хранилище выбранных товаров
user_orders = {}

# --- КЛАВИАТУРЫ ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ WEB МАГАЗИН", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("🏪 МАГАЗИН В БОТЕ", callback_data="shop_bot")],
        [InlineKeyboardButton("👤 МОЙ ПРОФИЛЬ", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ ПОДДЕРЖКА", callback_data="support")]
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
        stock = f" | {item['stock']} шт."
        btn_text = f"{item['name']} | {item['price']}₽{old_price}{stock}"
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
        [
            InlineKeyboardButton("✅ ПОДТВЕРДИТЬ", callback_data=f"confirm_{user_id}_{product}"),
            InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"decline_{user_id}")
        ],
        [InlineKeyboardButton("💬 ЗАПРОСИТЬ УТОЧНЕНИЕ", callback_data=f"ask_{user_id}")]
    ])

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = """
<tg-emoji emoji-id="5355272258979920753">👑</tg-emoji> <b>SAIKA PREMIUM STORE</b>

Привет! Ты находишься в @vpnsaika_bot

<tg-emoji emoji-id="6030445631921721471">🔥</tg-emoji> Качественные впн и многое другое только у нас

<tg-emoji emoji-id="5938413566624272793">🛒</tg-emoji> <b>Магазин</b> — выбор товаров
<tg-emoji emoji-id="5883964170268840032">👤</tg-emoji> <b>Профиль</b> — твои данные

Выбери действие ниже:
"""
    await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Назад в меню
    if data == "back_menu":
        await query.edit_message_text(
            "<b>🏠 ГЛАВНОЕ МЕНЮ</b>\n\nВыберите раздел:",
            reply_markup=main_menu(),
            parse_mode="HTML"
        )
    
    # Магазин в боте
    elif data == "shop_bot":
        text = (
            '<tg-emoji emoji-id="5938413566624272793">🛒</tg-emoji> <b>МАГАЗИН</b>\n\n'
            '<tg-emoji emoji-id="5350291836378307462">📋</tg-emoji> Выберите категорию:'
        )
        await query.edit_message_text(
            text,
            reply_markup=shop_categories(),
            parse_mode="HTML"
        )
    
    # Категории
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        titles = {"vpn": "🔒 VPN ДЛЯ PUBG", "extra": "📦 МАГНИТ & ПАКИ", "dns": "🌐 DNS СЕРВИСЫ"}
        text = f'<tg-emoji emoji-id="5350291836378307462">📋</tg-emoji> <b>{titles[category]}</b>\n\nВыберите товар:'
        await query.edit_message_text(
            text,
            reply_markup=products_keyboard(category),
            parse_mode="HTML"
        )
    
    # Выбор товара
    elif data.startswith("buy_"):
        _, category, product = data.split("_", 2)
        item = next((x for x in CATALOG[category] if x['name'] == product), None)
        
        if item:
            user_orders[query.from_user.id] = {"product": product, "price": item['price']}
            
            old_text = f" ❗{item['old']}₽" if item['old'] else ""
            text = f"""
<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>ОФОРМЛЕНИЕ ЗАКАЗА</b>

Товар: <b>{product}</b>
Цена: <b>{item['price']}₽</b>{old_text}
В наличии: {item['stock']} шт.

━━━━━━━━━━━━━━━━━━
<b>📋 РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:</b>

🏦 Банк: <b>Т-Банк</b>
💳 Карта: <code>2200 7021 4895 7363</code>
👤 Получатель: <b>Саид К.</b>

━━━━━━━━━━━━━━━━━━
<i>После оплаты нажмите кнопку ниже и загрузите скриншот чека</i>
"""
            await query.edit_message_text(
                text,
                reply_markup=payment_keyboard(product, item['price']),
                parse_mode="HTML"
            )
    
    # Кнопка "Я оплатил"
    elif data.startswith("paid_"):
        _, product, price = data.split("_", 2)
        text = f"""
<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>ЗАГРУЗИТЕ ЧЕК</b>

Товар: <b>{product}</b>
Сумма: <b>{price}₽</b>

📸 Отправьте скриншот оплаты <b>ПРЯМО В ЭТОТ ЧАТ</b>
💬 Можете добавить комментарий к фото

<i>Администратор проверит и отправит файлы</i>
"""
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ ОТМЕНА", callback_data="shop_bot")]
            ])
        )
        user_orders[query.from_user.id] = {"product": product, "price": price, "awaiting": "photo"}
    
    # Профиль
    elif data == "profile":
        user = query.from_user
        profile_text = f"""
<tg-emoji emoji-id="5883964170268840032">👤</tg-emoji> <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>

Имя: <b>{user.first_name} {user.last_name or ''}</b>
ID: <code>{user.id}</code>
Username: @{user.username or 'не указан'}

Статус: <tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> Premium Client

Для покупок откройте магазин 👇
"""
        await query.edit_message_text(profile_text, reply_markup=main_menu(), parse_mode="HTML")
    
    # Поддержка
    elif data == "support":
        support_text = """
<b>ℹ️ ПОДДЕРЖКА SAIKA STORE</b>

По всем вопросам:
• Оплата и получение файлов
• Технические проблемы
• Сотрудничество

Пишите: @saikasupport

<tg-emoji emoji-id="6030445631921721471">⚡</tg-emoji> <i>Работаем 24/7</i>
"""
        await query.edit_message_text(support_text, reply_markup=main_menu(), parse_mode="HTML")

# Обработка фото (чеков)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    caption = update.message.caption or ""
    
    order = user_orders.get(user.id, {})
    product = order.get('product', 'Неизвестный товар')
    price = order.get('price', '?')
    
    # Скачиваем фото
    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    
    # Отправляем админу
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
    
    # Уведомление пользователю
    await update.message.reply_text(
        f"""
<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>ЧЕК ПОЛУЧЕН!</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>
Статус: <code>⏳ ОЖИДАЕТ ПРОВЕРКИ</code>

Администратор проверит оплату и отправит файлы в этот чат.
Обычно это занимает 5-15 минут.
""",
        parse_mode="HTML",
        reply_markup=main_menu()
    )
    
    # Очищаем ожидание
    if user.id in user_orders:
        del user_orders[user.id]

# Обработка данных из WebApp
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = json.loads(update.effective_message.web_app_data.data)
    
    product = data.get('product')
    price = data.get('price')
    user_id = data.get('user_id')
    username = data.get('username')
    comment = data.get('comment', '')
    screenshot = data.get('screenshot')
    
    admin_msg = f"""
<b>🛒 НОВЫЙ ЗАКАЗ #{user_id} (WEB APP)</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>

Покупатель: @{username} (ID: <code>{user_id}</code>)
Время: {data.get('timestamp', 'только что')}

Комментарий: {comment or 'нет'}
"""
    
    if screenshot and screenshot.startswith('data:image'):
        try:
            image_data = base64.b64decode(screenshot.split(',')[1])
            image_file = BytesIO(image_data)
            image_file.name = f"check_{user_id}.jpg"
            
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=image_file,
                caption=admin_msg,
                reply_markup=admin_order_keyboard(user_id, product),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка загрузки скрина: {e}")
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_msg + f"\n\n❌ Ошибка загрузки скрина",
                reply_markup=admin_order_keyboard(user_id, product),
                parse_mode="HTML"
            )
    else:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_msg + "\n\n⚠️ Скриншот не прикреплен",
            reply_markup=admin_order_keyboard(user_id, product),
            parse_mode="HTML"
        )
    
    user_msg = f"""
<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>ЗАКАЗ ПРИНЯТ</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>
Статус: <code>⏳ ОЖИДАЕТ ПРОВЕРКИ</code>

Администратор проверит оплату и отправит файлы в этот чат.
Обычно это занимает 5-15 минут.
"""
    await update.effective_message.reply_text(user_msg, parse_mode="HTML")

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
<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji> <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>

Товар: <b>{product}</b>
Статус: <code>✅ УСПЕШНО</code>

Сейчас отправим файлы 👇
""",
            parse_mode="HTML"
        )
        
        files_sent = 0
        if product in PRODUCT_FILES:
            for file_path in PRODUCT_FILES[product]:
                try:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            await context.bot.send_document(
                                chat_id=user_id,
                                document=f,
                                caption=f"📁 Файл для {product}" if files_sent == 0 else ""
                            )
                        files_sent += 1
                except Exception as e:
                    logger.error(f"Ошибка отправки файла {file_path}: {e}")
        
        if files_sent == 0:
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Файлы готовятся, администратор отправит их вручную.\nОжидайте..."
            )
        
        await query.edit_message_caption(
            caption=query.message.caption + f"\n\n✅ <b>ПОДТВЕРЖДЕНО</b>\nФайлов отправлено: {files_sent}",
            parse_mode="HTML"
        )
    
    elif action == "decline":
        user_id = int(data[1])
        
        await context.bot.send_message(
            chat_id=user_id,
            text="""
❌ <b>ОПЛАТА НЕ ПОДТВЕРЖДЕНА</b>

Пожалуйста, проверьте:
• Правильность суммы
• Совпадение реквизитов
• Успешность транзакции

Если оплата прошла — отправьте скриншот в поддержку @saikasupport
""",
            parse_mode="HTML"
        )
        
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML"
        )
    
    elif action == "ask":
        user_id = int(data[1])
        
        await context.bot.send_message(
            chat_id=user_id,
            text="""
<tg-emoji emoji-id="6030445631921721471">💬</tg-emoji> <b>УТОЧНЕНИЕ ПО ЗАКАЗУ</b>

Администратор просит уточнить детали оплаты.
Пожалуйста, отправьте:
• Точное время платежа
• Сумму из истории транзакции
• Банк отправителя

Ответьте прямо в этот чат 👇
""",
            parse_mode="HTML"
        )
        
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n💬 <b>ЗАПРОШЕНО УТОЧНЕНИЕ</b>",
            parse_mode="HTML"
        )

# Обработка текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.effective_message.text
    
    # Если пользователь ожидал загрузку фото, но отправил текст
    if user.id in user_orders and user_orders[user.id].get('awaiting'):
        await update.message.reply_text(
            "📸 Пожалуйста, отправьте <b>ФОТО ЧЕКА</b>, а не текст.\n\nЕсли оплата не прошла - нажмите /start для нового заказа.",
            parse_mode="HTML"
        )
        return
    
    # Обычное сообщение - пересылаем админу
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"""
📨 <b>СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ</b>

От: @{user.username or user.first_name} (ID: <code>{user.id}</code>)

Сообщение:
{text}
""",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Ответить", url=f"tg://user?id={user.id}")]
        ])
    )
    
    await update.message.reply_text(
        "✅ Ваше сообщение отправлено администратору. Ожидайте ответа.",
        parse_mode="HTML"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(confirm|decline|ask)_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("🚀 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    os.makedirs("files", exist_ok=True)
    main()
