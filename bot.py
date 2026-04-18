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
WEBAPP_URL = "https://твой-сайт.com"  # ЗАМЕНИ НА URL ГДЕ ЛЕЖИТ HTML

# База файлов для товаров (замени на реальные пути к файлам)
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

# --- КЛАВИАТУРЫ ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ ОТКРЫТЬ МАГАЗИН", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("👤 МОЙ ПРОФИЛЬ", callback_data="profile")],
        [InlineKeyboardButton("ℹ️ ПОДДЕРЖКА", callback_data="support")]
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
    
    if query.data == "profile":
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
    
    elif query.data == "support":
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
    
    # Сообщение админу
    admin_msg = f"""
<b>🛒 НОВЫЙ ЗАКАЗ #{user_id}</b>

Товар: <b>{product}</b>
Сумма: <b>{price} ₽</b>

Покупатель: @{username} (ID: <code>{user_id}</code>)
Время: {data.get('timestamp', 'только что')}

Комментарий: {comment or 'нет'}
"""
    
    # Отправляем скриншот админу если есть
    if screenshot and screenshot.startswith('data:image'):
        try:
            # Декодируем base64
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
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_msg + f"\n\n❌ Ошибка загрузки скрина: {e}",
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
    
    # Сообщение пользователю
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
        
        # Уведомление пользователю
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
        
        # Отправка файлов
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
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"❌ Ошибка отправки файла: {e}\nСвяжитесь с поддержкой @saikasupport"
                    )
        
        if files_sent == 0:
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Файлы готовятся, администратор отправит их вручную.\nОжидайте..."
            )
        
        # Обновление сообщения админа
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

# Обработка ответа пользователя на уточнение
async def handle_user_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.effective_message.text
    
    # Пересылаем ответ админу
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"""
📨 <b>ОТВЕТ ОТ ПОЛЬЗОВАТЕЛЯ</b>

От: @{user.username or user.first_name} (ID: <code>{user.id}</code>)

Сообщение:
{text}
""",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Подтвердить заказ", callback_data=f"confirm_{user.id}_manual")],
            [InlineKeyboardButton("↩️ Ответить", url=f"tg://user?id={user.id}")]
        ])
    )
    
    await update.effective_message.reply_text(
        "✅ Ваше сообщение отправлено администратору. Ожидайте ответа.",
        parse_mode="HTML"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(profile|support)$"))
    app.add_handler(CallbackQueryHandler(admin_action, pattern="^(confirm|decline|ask)_"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_user_reply))
    
    print("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    # Создаем папку для файлов если её нет
    os.makedirs("files", exist_ok=True)
    main()
