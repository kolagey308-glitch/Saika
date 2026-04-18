import json
import logging
import base64
import os
import asyncio
from io import BytesIO
from datetime import datetime
import requests

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8451686285:AAFWffo20dsC1f3XSFpLKDtAQpZWmcgKJyM"
MAIN_ADMIN = 1471307057
SECOND_ADMIN = 7066870264
WEBAPP_URL = "https://saika-app-gamma.vercel.app"

SCREENSHOTS_DIR = "screenshots"
ORDERS_FILE = "orders_db.json"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# --- АВТОВЫДАЧА ТОВАРОВ ---
PRODUCT_FILES = {
    "GTR VPN": ["https://files.catbox.moe/cwy1n3.conf"],
    "VIP VPN": ["https://files.catbox.moe/ab8a1r.conf"],
    "ULTRA MAX VPN": ["https://files.catbox.moe/rqbq5r.conf"],
    "STRONG VPN": ["https://files.catbox.moe/e6a8yh.conf"],
    "SAIKA S1 VPN": ["https://files.catbox.moe/1coq6u.conf"],
    "DEAD ALL VPN": ["https://files.catbox.moe/ohvc5d.conf"],
    "TDM SKILL VPN": ["https://files.catbox.moe/ohvc5d.conf"],
    "FUCK VPN": ["https://files.catbox.moe/3ghk4a.conf"],
    "UNLY VPN": ["https://files.catbox.moe/5qcb3b.conf"],
    
    "Магнит андроид": ["https://files.catbox.moe/qahmjb.zip"],
    "Магнит ios": ["https://files.catbox.moe/ql2d0s.mobileconfig"],
    "Пак unly": ["https://files.catbox.moe/qahmjb.zip"],
    
    "DNS android": ["https://files.catbox.moe/ql2d0s.mobileconfig"],
    "DNS Ios": ["https://files.catbox.moe/ql2d0s.mobileconfig"],
}

# Специальные товары (выдаются ссылкой)
SPECIAL_PRODUCTS = {
    "Пак сайки": "https://www.icloud.com/shortcuts/83963f23bcc94e7a85bbbe0c6a56e350"
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
admin_state = {}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def emoji(id, char): 
    return f'<tg-emoji emoji-id="{id}">{char}</tg-emoji>'

def is_admin(user_id):
    return user_id in [MAIN_ADMIN, SECOND_ADMIN]

def admin_order_keyboard(order_id: str):
    return {
        "inline_keyboard": [
            [
                {"text": "✅ ПОДТВЕРДИТЬ", "callback_data": f"confirm_{order_id}"},
                {"text": "❌ ОТКЛОНИТЬ", "callback_data": f"decline_{order_id}"}
            ]
        ]
    }

def download_file(url):
    """Скачивает файл по URL и возвращает BytesIO"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return BytesIO(response.content)
    except Exception as e:
        logger.error(f"Ошибка скачивания {url}: {e}")
    return None

async def auto_send_product(bot, user_id, product_name):
    """Автоматическая отправка товара пользователю"""
    
    # Проверяем специальные товары (ссылки)
    if product_name in SPECIAL_PRODUCTS:
        await bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ <b>ЗАКАЗ ГОТОВ!</b>\n\n"
                f"Товар: <b>{product_name}</b>\n\n"
                f"🔗 <b>Ссылка для скачивания:</b>\n"
                f"{SPECIAL_PRODUCTS[product_name]}\n\n"
                f"Спасибо за покупку!"
            ),
            parse_mode="HTML"
        )
        return True
    
    # Проверяем обычные товары (файлы)
    if product_name in PRODUCT_FILES:
        files_sent = 0
        for file_url in PRODUCT_FILES[product_name]:
            file_data = download_file(file_url)
            if file_data:
                filename = file_url.split('/')[-1]
                
                # Определяем тип файла по расширению
                if filename.endswith('.conf'):
                    await bot.send_document(
                        chat_id=user_id,
                        document=file_data,
                        filename=filename,
                        caption=f"📁 {product_name}" if files_sent == 0 else ""
                    )
                elif filename.endswith(('.zip', '.mobileconfig')):
                    await bot.send_document(
                        chat_id=user_id,
                        document=file_data,
                        filename=filename,
                        caption=f"📁 {product_name}" if files_sent == 0 else ""
                    )
                elif filename.endswith(('.jpg', '.png', '.jpeg')):
                    await bot.send_photo(
                        chat_id=user_id,
                        photo=file_data,
                        caption=f"📁 {product_name}" if files_sent == 0 else ""
                    )
                else:
                    await bot.send_document(
                        chat_id=user_id,
                        document=file_data,
                        filename=filename,
                        caption=f"📁 {product_name}" if files_sent == 0 else ""
                    )
                files_sent += 1
        
        if files_sent > 0:
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ Все файлы отправлены! Спасибо за покупку!",
                parse_mode="HTML"
            )
            return True
        else:
            await bot.send_message(
                chat_id=user_id,
                text=f"❌ Ошибка загрузки файлов. Администратор отправит их вручную.",
                parse_mode="HTML"
            )
            return False
    
    return False

# --- КОМАНДЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=f'{emoji("5217822164362739968", "👑")} <b>SAIKA PREMIUM STORE</b>\n\nОткройте магазин:',
        reply_markup={"inline_keyboard": [[{"text": "🌐 ОТКРЫТЬ МАГАЗИН", "web_app": {"url": WEBAPP_URL}}]]},
        parse_mode="HTML"
    )

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
        
        if order.get('screenshot') and order['screenshot'].startswith('data:image'):
            try:
                screenshot_data = order['screenshot'].split(',')[1]
                image_data = base64.b64decode(screenshot_data)
                
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
        else:
            for admin_id in [MAIN_ADMIN, SECOND_ADMIN]:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_msg,
                    reply_markup=admin_order_keyboard(order_id),
                    parse_mode="HTML"
                )
        
        await update.effective_message.reply_text(
            f"{emoji('5217822164362739968', '👑')} <b>ЗАКАЗ ПРИНЯТ!</b>\n\n"
            f"Товар: {order['product']}\nСумма: {order['price']} ₽\nСтатус: ⏳ ОЖИДАЕТ",
            parse_mode="HTML"
        )

# --- Обработка кнопок админа ---
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
    
    order = next((o for o in orders_db if o['id'] == order_id), None)
    if not order:
        await query.answer("❌ Заказ не найден")
        return
    
    if action == "confirm":
        order['status'] = 'confirmed'
        save_orders(orders_db)
        
        await context.bot.send_message(
            chat_id=order['userId'],
            text=f"✅ <b>ОПЛАТА ПОДТВЕРЖДЕНА!</b>\n\nТовар: <b>{order['product']}</b>\n\nОтправляю файлы...",
            parse_mode="HTML"
        )
        
        # АВТОВЫДАЧА ТОВАРА
        success = await auto_send_product(context.bot, order['userId'], order['product'])
        
        if success:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ <b>ПОДТВЕРЖДЕНО И ОТПРАВЛЕНО</b>",
                parse_mode="HTML"
            )
            
            # Отзыв
            await context.bot.send_message(
                chat_id=order['userId'],
                text=(
                    f"{emoji('5440539497383087970', '📝')} <b>ОСТАВЬТЕ ОТЗЫВ</b> @saikamng\n\n"
                    f"{emoji('5314504236132747481', '💔')} СЛИЛ ТОВАР\n"
                    f"{emoji('5206607081334906820', '😡')} ИСПОРТИЛ ЕГО И ПОТЕРЯЛ ДЕНЬГИ"
                ),
                parse_mode="HTML"
            )
        else:
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n⚠️ <b>ПОДТВЕРЖДЕНО, НО ФАЙЛЫ НЕ НАЙДЕНЫ</b>",
                parse_mode="HTML",
                reply_markup={"inline_keyboard": [[{"text": "📁 ЗАГРУЗИТЬ ВРУЧНУЮ", "callback_data": f"uploadfile_{order_id}"}]]}
            )
    
    elif action == "decline":
        order['status'] = 'declined'
        save_orders(orders_db)
        
        await context.bot.send_message(
            chat_id=order['userId'],
            text=f"❌ <b>ОПЛАТА НЕ ПОДТВЕРЖДЕНА</b>\n\nТовар: {order['product']}\n\nПроверьте реквизиты.",
            parse_mode="HTML"
        )
        
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ <b>ОТКЛОНЕНО</b>",
            parse_mode="HTML"
        )
    
    elif action == "uploadfile":
        admin_state[user.id] = {"action": "upload_for_order", "order_id": order_id}
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n📁 <b>Отправьте файл для этого заказа</b>",
            parse_mode="HTML"
        )

# --- Обработка файлов от админа (ручная выдача) ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if is_admin(user.id) and user.id in admin_state:
        state = admin_state[user.id]
        if state.get("action") == "upload_for_order":
            order_id = state.get("order_id")
            order = next((o for o in orders_db if o['id'] == order_id), None)
            
            if order:
                photo = update.message.photo[-1]
                
                await context.bot.send_photo(
                    chat_id=order['userId'],
                    photo=photo.file_id,
                    caption=f"📁 Файл для {order['product']}"
                )
                
                await update.message.reply_text(f"✅ Файл отправлен пользователю {order['userId']}")
                del admin_state[user.id]

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if is_admin(user.id) and user.id in admin_state:
        state = admin_state[user.id]
        if state.get("action") == "upload_for_order":
            order_id = state.get("order_id")
            order = next((o for o in orders_db if o['id'] == order_id), None)
            
            if order:
                doc = update.message.document
                
                await context.bot.send_document(
                    chat_id=order['userId'],
                    document=doc.file_id,
                    caption=f"📁 {doc.file_name}"
                )
                
                await update.message.reply_text(f"✅ Файл отправлен пользователю {order['userId']}")
                del admin_state[user.id]

async def cleanup_webhook():
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook deleted")

def main():
    asyncio.run(cleanup_webhook())
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(confirm|decline|uploadfile)_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    logger.info("🚀 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
