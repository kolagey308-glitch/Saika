import asyncio
import json
import os
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict
import time
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== КОНФИГ ==========
BOT_TOKEN = "8614807346:AAHBgSk8b-EoKnBCe-p9wilWojBxYhC5V8I"
ADMIN_ID = 7496589494
CRYPTO_BOT_TOKEN = "560372:AAyQpvWZFSHpzrnVAhVwPF7PbcJmqI7bH0K"
UAH_CARD = "4441111008011946"
UAH_COMMENT = "За цифрові товари"

# ========== КАСТОМНЫЕ ЭМОДЗИ ID (Telegram Premium) ==========
# Твои ID эмодзи
PLAYCHEAT_EMOJI = "5931409969613116639"
STAR_EMOJI = "5805532930662996322"
CATALOG_EMOJI = "5208513917965328345"
PROFILE_EMOJI = "5886412370347036129"
PURCHASES_EMOJI = "5983399041197675256"
OXIDE_EMOJI = "5312048193444282508"
STANDOFF_EMOJI = "5819078828017849357"
BACK_MAIN_EMOJI = "5877629862306385808"
LEBRO_VIP_EMOJI = "5208422125924275090"
LEBRO_LITE_EMOJI = "5208422125924275090"
PERIOD_EMOJI = "5985596818912712352"
CRYPTO_EMOJI = "5361914370068613491"
UAH_EMOJI = "5805532930662996322"
BACK_PERIODS_EMOJI = "5877629862306385808"
INVOICE_EMOJI = "5983399041197675256"
SUM_EMOJI = "5208513917965328345"
PRODUCT_EMOJI = "5877260593903177342"
LINK_EMOJI = "5877465816030515018"
CHECK_EMOJI = "6005843436479975944"
CANCEL_EMOJI = "5985346521103604145"
CARD_EMOJI = "5208431570557360595"
RECEIPT_EMOJI = "6050592962730005028"
NO_KEY_EMOJI = "5208431570557360595"
RECEIPT_SENT_EMOJI = "5985596818912712352"
CONFIRMED_EMOJI = "5985596818912712352"
YOUR_KEY_EMOJI = "6005570495603282482"
THANKS_EMOJI = "5985596818912712352"
USER_ID_EMOJI = "5886505193180239900"
USERNAME_EMOJI = "5771887475421090729"
NAME_EMOJI = "5897962422169243693"
ACTIVE_KEY_EMOJI = "6005570495603282482"
EXPIRES_EMOJI = "5897962422169243693"
GAME_SELECT_EMOJI = "5960551395730919906"
LEBRO_NAME_EMOJI = "5877260593903177342"
TO_PAY_EMOJI = "5983399041197675256"
BACK_GAME_EMOJI = "5877629862306385808"
AGREE_EMOJI = "5985346521103604145"
RULES_1_EMOJI = "5985346521103604145"
RULES_2_EMOJI = "5985346521103604145"
RULES_3_EMOJI = "5985346521103604145"
RULES_4_EMOJI = "5985346521103604145"

# ========== ФОТО ==========
MENU_PHOTO = "https://files.catbox.moe/vz52pd.png"
CATALOG_PHOTO = "https://files.catbox.moe/w1ruj1.png"
GAME_SELECT_PHOTO = "https://files.catbox.moe/kxk5w3.png"
SYSTEM_PHOTO = "https://files.catbox.moe/87qpck.png"
PERIOD_PHOTO = "https://files.catbox.moe/b795ua.png"
PAYMENT_PHOTO = "https://files.catbox.moe/tzogel.png"

# ========== Цены и товары ==========
PRICES = {
    "Lebro_Lite": {"24h": 1.5, "7d": 4.5},
    "Lebro_VIP": {"24h": 3, "7d": 7.5, "30d": 15},
    "Plutonium": {"7d": 150, "30d": 300, "90d": 700},
}

PRODUCT_NAMES = {
    "Lebro_Lite": "Lebro [Lite]",
    "Lebro_VIP": "Lebro [VIP]",
    "Plutonium": "Plutonium"
}

PERIODS = {
    "Lebro_Lite": [("24 часа", "24h")],
    "Lebro_VIP": [("24 часа", "24h"), ("7 дней", "7d"), ("30 дней", "30d")],
    "Plutonium": [("7 дней", "7d"), ("30 дней", "30d"), ("90 дней", "90d")],
}

# ========== ДАННЫЕ ==========
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {}, 
        "pending_uah": {}, 
        "pending_crypto": {},
        "temp_invoices": {}
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# ========== FSM ==========
class States(StatesGroup):
    waiting_agreement = State()
    selecting_game = State()
    selecting_product = State()
    selecting_period = State()
    selecting_payment = State()
    waiting_uah_receipt = State()
    waiting_crypto_payment = State()
    admin_waiting_user_id = State()
    admin_waiting_key = State()
    admin_waiting_crypto_key = State()
    admin_waiting_uah_key = State()

# ========== ФУНКЦИЯ ДЛЯ ФОРМАТИРОВАНИЯ ТЕКСТА С ЭМОДЗИ ==========
def emoji(emoji_id: str) -> str:
    """Возвращает HTML тег для Telegram Premium эмодзи"""
    return f'<tg-emoji emoji-id="{emoji_id}"> </tg-emoji>'

# ========== КЛАВИАТУРЫ ==========

def agreement_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji(AGREE_EMOJI)} Я ознакомлен с правилами", callback_data="agree")]
    ])

def main_menu_keyboard(is_admin=False):
    buttons = [
        [
            InlineKeyboardButton(text=f"{emoji(CATALOG_EMOJI)} Каталог", callback_data="menu_catalog"),
            InlineKeyboardButton(text=f"{emoji(PROFILE_EMOJI)} Профиль", callback_data="menu_profile")
        ],
        [
            InlineKeyboardButton(text=f"{emoji(PURCHASES_EMOJI)} Мои покупки", callback_data="menu_purchases")
        ]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="🔧 Админ-панель", callback_data="menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Выдать ключ пользователю", callback_data="admin_give_key")],
        [InlineKeyboardButton(text=f"{emoji(UAH_EMOJI)} Подтвердить UAH оплату", callback_data="admin_confirm_uah")],
        [InlineKeyboardButton(text=f"{emoji(CRYPTO_EMOJI)} Подтвердить CRYPTO оплату", callback_data="admin_confirm_crypto")],
        [InlineKeyboardButton(text=f"{emoji(BACK_MAIN_EMOJI)} В главное меню", callback_data="back_to_main")]
    ])

def catalog_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji(OXIDE_EMOJI)} Oxide Survival Island", callback_data="game_oxide")],
        [InlineKeyboardButton(text=f"{emoji(STANDOFF_EMOJI)} Standoff 2", callback_data="game_standoff")],
        [InlineKeyboardButton(text=f"{emoji(BACK_MAIN_EMOJI)} В главное меню", callback_data="back_to_main")]
    ])

def products_keyboard(game):
    buttons = []
    if game == "oxide":
        buttons.append([InlineKeyboardButton(text=f"{emoji(LEBRO_VIP_EMOJI)} Lebro [VIP]", callback_data="product_Lebro_VIP")])
        buttons.append([InlineKeyboardButton(text=f"{emoji(LEBRO_LITE_EMOJI)} Lebro [Lite]", callback_data="product_Lebro_Lite")])
    else:
        buttons.append([InlineKeyboardButton(text="Plutonium", callback_data="product_Plutonium")])
    buttons.append([InlineKeyboardButton(text=f"{emoji(BACK_GAME_EMOJI)} Назад к играм", callback_data="back_to_catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def periods_keyboard(product):
    buttons = []
    for name, code in PERIODS[product]:
        buttons.append([InlineKeyboardButton(text=f"{emoji(PERIOD_EMOJI)} {name}", callback_data=f"period_{code}")])
    buttons.append([InlineKeyboardButton(text=f"{emoji(BACK_GAME_EMOJI)} Назад к продуктам", callback_data="back_to_products")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji(CRYPTO_EMOJI)} CryptoBot (USDT)", callback_data="pay_crypto")],
        [InlineKeyboardButton(text=f"{emoji(UAH_EMOJI)} Оплата гривной", callback_data="pay_uah")],
        [InlineKeyboardButton(text=f"{emoji(BACK_PERIODS_EMOJI)} Назад к периодам", callback_data="back_to_periods")]
    ])

def check_payment_keyboard(invoice_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji(CHECK_EMOJI)} Проверить оплату", callback_data=f"check_payment_{invoice_id}")],
        [InlineKeyboardButton(text=f"{emoji(CANCEL_EMOJI)} Отмена", callback_data="cancel_payment")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji(CANCEL_EMOJI)} Отмена", callback_data="cancel")]
    ])

def uah_receipt_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{emoji(CANCEL_EMOJI)} Отмена", callback_data="cancel")]
    ])

# ========== CRYPTOPAY API ==========

class CryptoPayAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://pay.crypt.bot/api"
    
    async def create_invoice(self, amount: float, currency: str = "USDT", description: str = "") -> Optional[Dict]:
        url = f"{self.base_url}/createInvoice"
        params = {"asset": currency, "amount": str(amount), "description": description[:100]}
        headers = {"Crypto-Pay-API-Token": self.token}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("ok"):
                            return result["result"]
                    return None
        except Exception as e:
            print(f"CryptoPay error: {e}")
            return None
    
    async def check_invoice(self, invoice_id) -> Optional[Dict]:
        url = f"{self.base_url}/getInvoices"
        params = {"invoice_ids": invoice_id}
        headers = {"Crypto-Pay-API-Token": self.token}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("ok") and result["result"].get("items"):
                            return result["result"]["items"][0]
                    return None
        except Exception as e:
            print(f"Check invoice error: {e}")
            return None

crypto_api = CryptoPayAPI(CRYPTO_BOT_TOKEN)

# ========== ФУНКЦИИ ==========

def register_user(user_id, username, full_name):
    if str(user_id) not in data["users"]:
        data["users"][str(user_id)] = {
            "user_id": user_id,
            "username": username or "Нет",
            "full_name": full_name,
            "active_key": None,
            "active_product": None,
            "expires_at": None,
            "purchases": [],
            "agreed": False
        }
        save_data()

def add_purchase(user_id, product_name, period, price, currency, key, status="pending"):
    purchase = {
        "product": product_name,
        "period": period,
        "price": price,
        "currency": currency,
        "key": key if key else "Ожидает выдачи",
        "purchased_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status
    }
    data["users"][str(user_id)]["purchases"].append(purchase)
    
    if status == "active" and key:
        data["users"][str(user_id)]["active_key"] = key
        data["users"][str(user_id)]["active_product"] = product_name
        days = 1 if period == "24h" else int(period.replace("d", ""))
        expires = datetime.now() + timedelta(days=days)
        data["users"][str(user_id)]["expires_at"] = expires.strftime("%Y-%m-%d %H:%M:%S")
    
    save_data()

def activate_key(user_id, key, product_name, period):
    data["users"][str(user_id)]["active_key"] = key
    data["users"][str(user_id)]["active_product"] = product_name
    days = 1 if period == "24h" else int(period.replace("d", ""))
    expires = datetime.now() + timedelta(days=days)
    data["users"][str(user_id)]["expires_at"] = expires.strftime("%Y-%m-%d %H:%M:%S")
    
    for purchase in reversed(data["users"][str(user_id)]["purchases"]):
        if purchase["product"] == product_name and purchase["period"] == period and purchase["status"] == "pending":
            purchase["status"] = "active"
            purchase["key"] = key
            break
    save_data()

async def send_photo_with_caption(chat_id, photo_url, caption, reply_markup=None):
    await bot.send_photo(
        chat_id=chat_id,
        photo=photo_url,
        caption=caption,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ========== БОТ ==========

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def is_admin(user_id):
    return user_id == ADMIN_ID

# ========== ОСНОВНЫЕ ХЭНДЛЕРЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    if not data["users"][str(message.from_user.id)]["agreed"]:
        rules = f"""{emoji(PLAYCHEAT_EMOJI)} <b>Правила PlayCheatGameBot</b>

{emoji(RULES_1_EMOJI)} <b>1. Возврат:</b> Возврата нет — при покупке цифрового товара потеря, неправильное использование никто не компенсирует.

{emoji(RULES_2_EMOJI)} <b>2. Ответственность:</b> Исполнитель не несёт ответственности за последствия применения.

{emoji(RULES_3_EMOJI)} <b>3. Общие:</b> Оплачивая услугу, вы соглашаетесь с данными правилами.

{emoji(RULES_4_EMOJI)} <b>4. Заключительные:</b> Исполнитель вправе изменять условия.

{emoji(AGREE_EMOJI)} Нажмите на кнопку ниже, чтобы продолжить"""
        await message.answer(rules, parse_mode="HTML", reply_markup=agreement_keyboard())
        await state.set_state(States.waiting_agreement)
    else:
        await show_main_menu(message.chat.id)

@dp.callback_query(F.data == "agree")
async def agree_rules(callback: types.CallbackQuery, state: FSMContext):
    data["users"][str(callback.from_user.id)]["agreed"] = True
    save_data()
    await callback.message.delete()
    await show_main_menu(callback.message.chat.id)
    await state.clear()

async def show_main_menu(chat_id):
    text = f"""{emoji(PLAYCHEAT_EMOJI)} <b>PlayCheatGameBot - Надёжный магазин читов</b>

{emoji(STAR_EMOJI)} <b>Почему мы?</b>
• Моментальная выдача после оплаты
• Работает на всех устройствах (NO ROOT)
• Анонимная оплата криптовалютой
• 24/7 поддержка
• Проверенные софты

<b>Выберите действие:</b>"""
    await send_photo_with_caption(chat_id, MENU_PHOTO, text, main_menu_keyboard(is_admin(chat_id)))

# ========== КАТАЛОГ ==========

@dp.callback_query(F.data == "menu_catalog")
async def menu_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = f"{emoji(GAME_SELECT_EMOJI)} <b>Выберите игру:</b>"
    await send_photo_with_caption(callback.message.chat.id, CATALOG_PHOTO, text, catalog_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "game_oxide")
async def game_oxide(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(game="oxide")
    text = f"{emoji(STANDOFF_EMOJI)} <b>Oxide Survival Island - Выберите софт:</b>"
    await send_photo_with_caption(callback.message.chat.id, GAME_SELECT_PHOTO, text, products_keyboard("oxide"))
    await callback.answer()

@dp.callback_query(F.data == "game_standoff")
async def game_standoff(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(game="standoff")
    text = f"{emoji(STANDOFF_EMOJI)} <b>Standoff 2 - Выберите софт:</b>"
    await send_photo_with_caption(callback.message.chat.id, GAME_SELECT_PHOTO, text, products_keyboard("standoff"))
    await callback.answer()

@dp.callback_query(F.data.startswith("product_"))
async def select_product(callback: types.CallbackQuery, state: FSMContext):
    product = callback.data.replace("product_", "")
    await state.update_data(product=product)
    product_name = PRODUCT_NAMES[product]
    text = f"{emoji(LEBRO_NAME_EMOJI)} <b>{product_name}</b>\n\nВыберите период действия:"
    await send_photo_with_caption(callback.message.chat.id, SYSTEM_PHOTO, text, periods_keyboard(product))
    await callback.answer()

@dp.callback_query(F.data.startswith("period_"))
async def select_period(callback: types.CallbackQuery, state: FSMContext):
    period = callback.data.replace("period_", "")
    await state.update_data(period=period)
    
    data_state = await state.get_data()
    product = data_state["product"]
    price = PRICES[product][period]
    currency = "USDT" if "Lebro" in product else "UAH"
    
    text = f"{emoji(TO_PAY_EMOJI)} <b>К оплате: {price} {currency}</b>\n\nВыберите способ оплаты:"
    await send_photo_with_caption(callback.message.chat.id, PAYMENT_PHOTO, text, payment_keyboard())
    await callback.answer()

# ========== CRYPTO ОПЛАТА ==========

@dp.callback_query(F.data == "pay_crypto")
async def pay_crypto(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state.get("product")
    period = data_state.get("period")
    
    if not product or not period:
        await callback.answer("❌ Ошибка: выберите товар заново", show_alert=True)
        await show_main_menu(callback.message.chat.id)
        return
    
    product_name = PRODUCT_NAMES[product]
    price = PRICES[product][period]
    
    invoice = await crypto_api.create_invoice(price, "USDT", f"{product_name} {period}")
    
    if not invoice:
        text = "❌ Ошибка создания счета. Попробуйте позже."
        await callback.message.edit_caption(caption=text, reply_markup=payment_keyboard())
        await callback.answer()
        return
    
    invoice_id = invoice["invoice_id"]
    pay_url = invoice["pay_url"]
    
    auto_key = f"AUTO-{product_name[:4]}-{period}-{random.randint(1000, 9999)}"
    
    data["pending_crypto"][str(invoice_id)] = {
        "user_id": callback.from_user.id,
        "product": product,
        "period": period,
        "product_name": product_name,
        "price": price,
        "created_at": time.time(),
        "key": auto_key
    }
    data["temp_invoices"][str(invoice_id)] = {
        "user_id": callback.from_user.id,
        "product": product,
        "period": period,
        "product_name": product_name,
        "price": price,
        "key": auto_key
    }
    save_data()
    
    text = f"""{emoji(INVOICE_EMOJI)} <b>Создан счет на оплату</b>

{emoji(SUM_EMOJI)} <b>Сумма:</b> {price} USDT
{emoji(PRODUCT_EMOJI)} <b>Товар:</b> {product_name} ({period})

{emoji(LINK_EMOJI)} <b>Ссылка для оплаты:</b> <a href="{pay_url}">Оплатить</a>

{emoji(CHECK_EMOJI)} После оплаты нажмите кнопку ниже для проверки"""
    
    await callback.message.edit_caption(caption=text, reply_markup=check_payment_keyboard(invoice_id))
    await state.update_data(crypto_invoice_id=invoice_id)
    await state.set_state(States.waiting_crypto_payment)
    await callback.answer()

@dp.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: types.CallbackQuery, state: FSMContext):
    invoice_id = int(callback.data.replace("check_payment_", ""))
    
    invoice_info = data["temp_invoices"].get(str(invoice_id))
    if not invoice_info:
        await callback.answer("❌ Счет не найден", show_alert=True)
        return
    
    invoice = await crypto_api.check_invoice(invoice_id)
    
    if not invoice:
        await callback.answer("❌ Ошибка проверки", show_alert=True)
        return
    
    status = invoice.get("status")
    
    if status == "paid":
        user_id = invoice_info["user_id"]
        product_name = invoice_info["product_name"]
        period = invoice_info["period"]
        price = invoice_info["price"]
        auto_key = invoice_info.get("key", f"KEY-{user_id}-{int(time.time())}")
        
        add_purchase(user_id, product_name, period, price, "USDT", auto_key, status="active")
        activate_key(user_id, auto_key, product_name, period)
        
        if str(invoice_id) in data["pending_crypto"]:
            del data["pending_crypto"][str(invoice_id)]
        if str(invoice_id) in data["temp_invoices"]:
            del data["temp_invoices"][str(invoice_id)]
        save_data()
        
        text = f"""{emoji(CONFIRMED_EMOJI)} <b>Оплата подтверждена!</b>

{emoji(SUM_EMOJI)} <b>Сумма:</b> {price} USDT
{emoji(PRODUCT_EMOJI)} <b>Товар:</b> {product_name} ({period})
{emoji(YOUR_KEY_EMOJI)} <b>Ваш ключ:</b> <code>{auto_key}</code>

{emoji(THANKS_EMOJI)} Спасибо за покупку!"""
        
        await callback.message.edit_caption(caption=text)
        
        await bot.send_message(
            ADMIN_ID,
            f"✅ <b>CRYPTO ОПЛАТА</b>\n\n"
            f"👤 Пользователь: @{callback.from_user.username or 'Нет'} (ID: {user_id})\n"
            f"📦 Товар: {product_name} ({period})\n"
            f"💰 Сумма: {price} USDT\n"
            f"🔑 Ключ: <code>{auto_key}</code>",
            parse_mode="HTML"
        )
        
        await state.clear()
        
    elif status == "expired":
        await callback.answer("❌ Счет просрочен. Создайте новый.", show_alert=True)
    else:
        await callback.answer(f"⏳ Статус: {status}. Оплата не обнаружена.", show_alert=True)

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback.message.chat.id)
    await callback.answer("Оплата отменена")

# ========== UAH ОПЛАТА ==========

@dp.callback_query(F.data == "pay_uah")
async def pay_uah(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state.get("product")
    period = data_state.get("period")
    
    if not product or not period:
        await callback.answer("❌ Ошибка: выберите товар заново", show_alert=True)
        await show_main_menu(callback.message.chat.id)
        return
    
    product_name = PRODUCT_NAMES[product]
    price = PRICES[product][period]
    
    await state.update_data(uah_product=product, uah_period=period, uah_price=price, uah_product_name=product_name)
    
    text = f"""{emoji(PERIOD_EMOJI)} <b>Оплата гривной</b>

{emoji(SUM_EMOJI)} <b>Сумма:</b> {price} грн
{emoji(PRODUCT_EMOJI)} <b>Товар:</b> {product_name} ({period})

{emoji(CARD_EMOJI)} <b>Карта для оплаты:</b> <code>{UAH_CARD}</code>
❗ <b>Комментарий:</b> <code>{UAH_COMMENT}</code>

{emoji(RECEIPT_EMOJI)} <b>После оплаты отправьте скриншот чека сюда</b>

{emoji(NO_KEY_EMOJI)} Без чека ключ НЕ будет выдан"""
    
    await callback.message.edit_caption(caption=text, reply_markup=uah_receipt_keyboard())
    await state.set_state(States.waiting_uah_receipt)
    await callback.answer()

@dp.message(States.waiting_uah_receipt, F.photo)
async def receive_uah_receipt(message: types.Message, state: FSMContext):
    data_state = await state.get_data()
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    
    pending_id = f"uah_{user_id}_{int(datetime.now().timestamp())}"
    data["pending_uah"][pending_id] = {
        "user_id": user_id,
        "product": data_state["uah_product_name"],
        "period": data_state["uah_period"],
        "price": data_state["uah_price"],
        "photo": photo_id,
        "username": message.from_user.username or "Нет",
        "product_code": data_state["uah_product"],
        "period_code": data_state["uah_period"]
    }
    save_data()
    
    admin_text = f"""🔔 <b>НОВАЯ ОПЛАТА UAH</b>

👤 Пользователь: @{message.from_user.username or 'Нет'} (ID: {user_id})
📦 Товар: {data_state['uah_product_name']} ({data_state['uah_period']})
💰 Сумма: {data_state['uah_price']} грн

🆔 ID чека: <code>{pending_id}</code>

Используйте <b>Админ-панель → Подтвердить UAH оплату</b> для выдачи"""
    
    await bot.send_photo(ADMIN_ID, photo_id, caption=admin_text, parse_mode="HTML")
    
    text = f"{emoji(RECEIPT_SENT_EMOJI)} Чек отправлен! Администратор выдаст ключ после проверки."
    await message.answer(text, parse_mode="HTML")
    await state.clear()

# ========== ПРОФИЛЬ И ПОКУПКИ ==========

@dp.callback_query(F.data == "menu_profile")
async def menu_profile(callback: types.CallbackQuery):
    user = data["users"][str(callback.from_user.id)]
    
    active = user.get("active_key") or "Нет активного ключа"
    product = user.get("active_product") or "—"
    expires = user.get("expires_at") or "—"
    
    text = f"""{emoji(PROFILE_EMOJI)} <b>Ваш профиль</b>

{emoji(USER_ID_EMOJI)} <b>ID:</b> <code>{user['user_id']}</code>
{emoji(USERNAME_EMOJI)} <b>Юзернейм:</b> @{user['username']}
{emoji(NAME_EMOJI)} <b>Имя:</b> {user['full_name']}

{emoji(ACTIVE_KEY_EMOJI)} <b>Активный ключ:</b> <code>{active}</code>
{emoji(PRODUCT_EMOJI)} <b>Товар:</b> {product}
{emoji(EXPIRES_EMOJI)} <b>Срок до:</b> {expires}"""
    
    await callback.message.edit_caption(caption=text, reply_markup=main_menu_keyboard(is_admin(callback.from_user.id)))
    await callback.answer()

@dp.callback_query(F.data == "menu_purchases")
async def menu_purchases(callback: types.CallbackQuery):
    purchases = data["users"][str(callback.from_user.id)].get("purchases", [])
    
    if not purchases:
        text = "📭 <b>У вас пока нет покупок</b>\n\nИспользуйте Каталог для приобретения читов."
    else:
        text = f"{emoji(PURCHASES_EMOJI)} <b>ИСТОРИЯ ПОКУПОК:</b>\n\n"
        for i, p in enumerate(reversed(purchases[-10:]), 1):
            status_emoji = "✅" if p['status'] == 'active' else "⏳"
            text += f"{i}. {status_emoji} <b>{p['product']}</b>\n"
            text += f"   Период: {p['period']}\n"
            text += f"   Цена: {p['price']} {p['currency']}\n"
            text += f"   Ключ: <code>{p['key']}</code>\n"
            text += f"   Дата: {p['purchased_at']}\n\n"
    
    await callback.message.edit_caption(caption=text, reply_markup=main_menu_keyboard(is_admin(callback.from_user.id)))
    await callback.answer()

# ========== АДМИН-ПАНЕЛЬ (остальные функции такие же как в предыдущем коде) ==========

# ... (продолжение следует - остальные админ функции остаются без изменений)

# ========== НАВИГАЦИЯ ==========

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback.message.chat.id)
    await callback.answer()

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = f"{emoji(GAME_SELECT_EMOJI)} <b>Выберите игру:</b>"
    await send_photo_with_caption(callback.message.chat.id, CATALOG_PHOTO, text, catalog_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_products")
async def back_to_products(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    game = data_state.get("game", "oxide")
    text = f"{emoji(STANDOFF_EMOJI)} <b>{'Oxide Survival Island' if game == 'oxide' else 'Standoff 2'} - Выберите софт:</b>"
    await send_photo_with_caption(callback.message.chat.id, GAME_SELECT_PHOTO, text, products_keyboard(game))
    await callback.answer()

@dp.callback_query(F.data == "back_to_periods")
async def back_to_periods(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state.get("product")
    if not product:
        await callback.answer("❌ Ошибка, выберите товар заново", show_alert=True)
        await show_main_menu(callback.message.chat.id)
        return
    product_name = PRODUCT_NAMES[product]
    text = f"{emoji(LEBRO_NAME_EMOJI)} <b>{product_name}</b>\n\nВыберите период:"
    await send_photo_with_caption(callback.message.chat.id, PERIOD_PHOTO, text, periods_keyboard(product))
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback.message.chat.id)
    await callback.answer("Действие отменено")

# ========== ЗАПУСК ==========

async def main():
    print("✅ Бот запущен!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("📦 Жду команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
