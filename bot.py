import asyncio
import json
import os
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict
import time

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
EMOJI = {
    "playcheat": "5931409969613116639",  # PlayCheatGameBot
    "star": "5805532930662996322",       # Почему мы? / Оплата гривной
    "catalog": "5208513917965328345",    # Каталог
    "profile": "5886412370347036129",    # Профиль
    "purchases": "5983399041197675256",  # Мои покупки
    "oxide": "5312048193444282508",      # Oxide Survival Island
    "standoff": "5819078828017849357",   # Standoff 2
    "back_main": "5877629862306385808",  # В главное меню / Назад к играм
    "lebro_vip": "5208422125924275090",  # Lebro [VIP]
    "lebro_lite": "5208422125924275090", # Lebro [Lite]
    "period": "5985596818912712352",     # Эмодзи для периодов
    "crypto": "5361914370068613491",     # CryptoBot (USDT)
    "uah": "5805532930662996322",        # Оплата гривной
    "back_periods": "5877629862306385808", # назад к периодам
    "invoice": "5983399041197675256",    # Создан счет
    "sum": "5208513917965328345",        # Сумма
    "product": "5877260593903177342",    # Товар
    "link": "5877465816030515018",       # Ссылка для оплаты
    "check": "6005843436479975944",      # Проверить оплату
    "cancel": "5985346521103604145",     # Отмена
    "card": "5208431570557360595",       # Карта для оплаты
    "receipt": "6050592962730005028",    # После оплаты отправьте скриншот
    "no_key": "5208431570557360595",     # Без чека ключ НЕ будет выдан
    "receipt_sent": "5985596818912712352", # Чек отправлен
    "confirmed": "5985596818912712352",  # Ваша UAH оплата подтверждена
    "your_key": "6005570495603282482",   # Ваш ключ
    "thanks": "5985596818912712352",     # Спасибо за покупку
    "user_id": "5886505193180239900",    # ID
    "username": "5771887475421090729",   # Юзернейм
    "name": "5897962422169243693",       # Имя
    "active_key": "6005570495603282482", # Активный ключ
    "expires": "5897962422169243693",    # Срок до
    "game_select": "5960551395730919906", # Выберите игру
    "lebroname": "5877260593903177342",  # Lebro (Vip или Lite)
    "to_pay": "5983399041197675256",     # К оплате
    "back_game": "5877629862306385808",  # Назад к играм
}

# Цены и товары
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

# ========== ФУНКЦИЯ ДЛЯ СОЗДАНИЯ КНОПОК С ЭМОДЗИ ==========
def make_button(text: str, callback_data: str, emoji_id: str = None, style: str = None) -> InlineKeyboardButton:
    """Создает кнопку с кастомным эмодзи"""
    if emoji_id:
        text = f'<tg-emoji emoji-id="{emoji_id}"> </tg-emoji>{text}'
    return InlineKeyboardButton(text=text, callback_data=callback_data)

def make_inline_keyboard(buttons_data: list) -> InlineKeyboardMarkup:
    """Создает инлайн клавиатуру из списка кнопок"""
    keyboard = []
    for row in buttons_data:
        keyboard_row = []
        for btn in row:
            style = btn.get("style")
            # Для премиум стилей используем специальный параметр
            if style == "danger":
                keyboard_row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]))
            elif style == "success":
                keyboard_row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]))
            elif style == "primary":
                keyboard_row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]))
            else:
                keyboard_row.append(InlineKeyboardButton(text=btn["text"], callback_data=btn["callback_data"]))
        keyboard.append(keyboard_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== КЛАВИАТУРЫ ==========

def agreement_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("✅ Я ознакомлен с правилами", "agree", None)]
    ])

def main_menu_keyboard(is_admin=False):
    buttons = [
        [
            make_button("Каталог", "menu_catalog", EMOJI["catalog"]),
            make_button("Профиль", "menu_profile", EMOJI["profile"])
        ],
        [
            make_button("Мои покупки", "menu_purchases", EMOJI["purchases"])
        ]
    ]
    if is_admin:
        buttons.append([make_button("🔧 Админ-панель", "menu_admin", None)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("🔑 Выдать ключ пользователю", "admin_give_key", None)],
        [make_button("💰 Подтвердить UAH оплату", "admin_confirm_uah", None)],
        [make_button("💎 Подтвердить CRYPTO оплату", "admin_confirm_crypto", None)],
        [make_button("В главное меню", "back_to_main", EMOJI["back_main"])]
    ])

def catalog_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("Oxide Survival Island", "game_oxide", EMOJI["oxide"])],
        [make_button("Standoff 2", "game_standoff", EMOJI["standoff"])],
        [make_button("В главное меню", "back_to_main", EMOJI["back_main"])]
    ])

def products_keyboard(game):
    buttons = []
    if game == "oxide":
        buttons.append([make_button("Lebro [VIP]", "product_Lebro_VIP", EMOJI["lebro_vip"])])
        buttons.append([make_button("Lebro [Lite]", "product_Lebro_Lite", EMOJI["lebro_lite"])])
    else:
        buttons.append([make_button("Plutonium", "product_Plutonium", None)])
    buttons.append([make_button("Назад к играм", "back_to_catalog", EMOJI["back_game"])])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def periods_keyboard(product):
    buttons = []
    for name, code in PERIODS[product]:
        buttons.append([make_button(f'{name}', f"period_{code}", EMOJI["period"])])
    buttons.append([make_button("Назад к продуктам", "back_to_products", EMOJI["back_game"])])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("CryptoBot (USDT)", "pay_crypto", EMOJI["crypto"])],
        [make_button("Оплата гривной", "pay_uah", EMOJI["uah"])],
        [make_button("Назад к периодам", "back_to_periods", EMOJI["back_periods"])]
    ])

def check_payment_keyboard(invoice_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("Проверить оплату", f"check_payment_{invoice_id}", EMOJI["check"])],
        [make_button("Отмена", "cancel_payment", EMOJI["cancel"])]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("Отмена", "cancel", EMOJI["cancel"])]
    ])

def uah_receipt_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [make_button("Отмена", "cancel", EMOJI["cancel"])]
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

def format_with_emoji(text: str) -> str:
    """Заменяет маркеры на кастомные эмодзи"""
    replacements = {
        "{playcheat}": f'<tg-emoji emoji-id="{EMOJI["playcheat"]}"> </tg-emoji>',
        "{star}": f'<tg-emoji emoji-id="{EMOJI["star"]}"> </tg-emoji>',
        "{profile}": f'<tg-emoji emoji-id="{EMOJI["profile"]}"> </tg-emoji>',
        "{catalog}": f'<tg-emoji emoji-id="{EMOJI["catalog"]}"> </tg-emoji>',
        "{purchases}": f'<tg-emoji emoji-id="{EMOJI["purchases"]}"> </tg-emoji>',
        "{check}": f'<tg-emoji emoji-id="{EMOJI["check"]}"> </tg-emoji>',
        "{cancel}": f'<tg-emoji emoji-id="{EMOJI["cancel"]}"> </tg-emoji>',
        "{confirmed}": f'<tg-emoji emoji-id="{EMOJI["confirmed"]}"> </tg-emoji>',
        "{key_icon}": f'<tg-emoji emoji-id="{EMOJI["your_key"]}"> </tg-emoji>',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

# ========== БОТ ==========

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

def is_admin(user_id):
    return user_id == ADMIN_ID

async def send_with_emoji(chat_id, text, keyboard=None):
    """Отправляет сообщение с HTML разметкой и эмодзи"""
    formatted_text = format_with_emoji(text)
    await bot.send_message(chat_id=chat_id, text=formatted_text, reply_markup=keyboard)

# ========== ОСНОВНЫЕ ХЭНДЛЕРЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    if not data["users"][str(message.from_user.id)]["agreed"]:
        rules = """📜 <b>Правила PlayCheatGameBot</b> 

🚫 <b>1. Возврат:</b> Возврата нет — при покупке цифрового товара потеря, неправильное использование никто не компенсирует.

⚠️ <b>2. Ответственность:</b> Исполнитель не несёт ответственности за последствия применения.

📜 <b>3. Общие:</b> Оплачивая услугу, вы соглашаетесь с данными правилами.

🛡 <b>4. Заключительные:</b> Исполнитель вправе изменять условия.

✅ Нажмите на кнопку ниже, чтобы продолжить"""
        await message.answer(rules, reply_markup=agreement_keyboard())
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
    text = """<tg-emoji emoji-id="5931409969613116639"> </tg-emoji> <b>PlayCheatGameBot - Надёжный магазин читов</b>

<tg-emoji emoji-id="5805532930662996322"> </tg-emoji> <b>Почему мы?</b>
• Моментальная выдача после оплаты
• Работает на всех устройствах (NO ROOT)
• Анонимная оплата криптовалютой
• 24/7 поддержка
• Проверенные софты

<b>Выберите действие:</b>"""
    await send_with_emoji(chat_id, text, main_menu_keyboard(is_admin(chat_id)))

# КАТАЛОГ
@dp.callback_query(F.data == "menu_catalog")
async def menu_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "<tg-emoji emoji-id=\"5960551395730919906\"> </tg-emoji> <b>Выберите игру:</b>"
    await send_with_emoji(callback.message.chat.id, text, catalog_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "game_oxide")
async def game_oxide(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(game="oxide")
    text = "<tg-emoji emoji-id=\"5819078828017849357\"> </tg-emoji> <b>Oxide Survival Island - Выберите софт:</b>"
    await send_with_emoji(callback.message.chat.id, text, products_keyboard("oxide"))
    await callback.answer()

@dp.callback_query(F.data == "game_standoff")
async def game_standoff(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(game="standoff")
    text = "<tg-emoji emoji-id=\"5819078828017849357\"> </tg-emoji> <b>Standoff 2 - Выберите софт:</b>"
    await send_with_emoji(callback.message.chat.id, text, products_keyboard("standoff"))
    await callback.answer()

@dp.callback_query(F.data.startswith("product_"))
async def select_product(callback: types.CallbackQuery, state: FSMContext):
    product = callback.data.replace("product_", "")
    await state.update_data(product=product)
    product_name = PRODUCT_NAMES[product]
    text = f"<tg-emoji emoji-id=\"5877260593903177342\"> </tg-emoji> <b>{product_name}</b>\n\nВыберите период действия:"
    await send_with_emoji(callback.message.chat.id, text, periods_keyboard(product))
    await callback.answer()

@dp.callback_query(F.data.startswith("period_"))
async def select_period(callback: types.CallbackQuery, state: FSMContext):
    period = callback.data.replace("period_", "")
    await state.update_data(period=period)
    
    data_state = await state.get_data()
    product = data_state["product"]
    price = PRICES[product][period]
    currency = "USDT" if "Lebro" in product else "UAH"
    
    text = f"<tg-emoji emoji-id=\"5983399041197675256\"> </tg-emoji> <b>К оплате: {price} {currency}</b>\n\nВыберите способ оплаты:"
    await send_with_emoji(callback.message.chat.id, text, payment_keyboard())
    await callback.answer()

# ========== CRYPTO ОПЛАТА ==========

@dp.callback_query(F.data == "pay_crypto")
async def pay_crypto(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state["product"]
    period = data_state["period"]
    product_name = PRODUCT_NAMES[product]
    price = PRICES[product][period]
    
    invoice = await crypto_api.create_invoice(price, "USDT", f"{product_name} {period}")
    
    if not invoice:
        text = "❌ Ошибка создания счета. Попробуйте позже."
        await callback.message.edit_text(text, reply_markup=payment_keyboard())
        await callback.answer()
        return
    
    invoice_id = invoice["invoice_id"]
    pay_url = invoice["pay_url"]
    
    data["pending_crypto"][str(invoice_id)] = {
        "user_id": callback.from_user.id,
        "product": product,
        "period": period,
        "product_name": product_name,
        "price": price,
        "created_at": time.time()
    }
    data["temp_invoices"][str(invoice_id)] = {
        "user_id": callback.from_user.id,
        "product": product,
        "period": period,
        "product_name": product_name,
        "price": price
    }
    save_data()
    
    text = f"""<tg-emoji emoji-id="5983399041197675256"> </tg-emoji> <b>Создан счет на оплату</b>

<tg-emoji emoji-id="5208513917965328345"> </tg-emoji> <b>Сумма:</b> {price} USDT
<tg-emoji emoji-id="5877260593903177342"> </tg-emoji> <b>Товар:</b> {product_name} ({period})

<tg-emoji emoji-id="5877465816030515018"> </tg-emoji> <b>Ссылка для оплаты:</b> <a href="{pay_url}">Оплатить</a>

<tg-emoji emoji-id="6005843436479975944"> </tg-emoji> После оплаты нажмите кнопку ниже для проверки"""
    
    await callback.message.edit_text(text, reply_markup=check_payment_keyboard(invoice_id))
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
        pending_id = f"crypto_{invoice_id}"
        data["pending_crypto"][pending_id] = {
            "user_id": user_id,
            "product": invoice_info["product"],
            "period": invoice_info["period"],
            "product_name": invoice_info["product_name"],
            "price": invoice_info["price"],
            "invoice_id": invoice_id
        }
        save_data()
        
        text = f"""✅ <b>Оплата подтверждена!</b>

💰 Сумма: {invoice_info['price']} USDT оплачена
📦 Товар: {invoice_info['product_name']} ({invoice_info['period']})

⏳ Ожидайте выдачи ключа от администратора...
Администратор уже уведомлен."""
        
        await callback.message.edit_text(text)
        
        await bot.send_message(
            ADMIN_ID,
            f"🔔 <b>НОВАЯ CRYPTO ОПЛАТА</b>\n\n"
            f"👤 Пользователь: @{callback.from_user.username or 'Нет'} (ID: {user_id})\n"
            f"📦 Товар: {invoice_info['product_name']} ({invoice_info['period']})\n"
            f"💰 Сумма: {invoice_info['price']} USDT\n"
            f"🆔 Invoice: {invoice_id}\n\n"
            f"Используйте <b>Админ-панель → Подтвердить CRYPTO оплату</b> для выдачи ключа",
            parse_mode="HTML"
        )
        await state.clear()
    elif status == "expired":
        await callback.answer("❌ Счет просрочен. Создайте новый.", show_alert=True)
    else:
        await callback.answer(f"⏳ Статус: {status}. Оплата не обнаружена", show_alert=True)

@dp.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback.message.chat.id)
    await callback.answer("Оплата отменена")

# ========== UAH ОПЛАТА ==========

@dp.callback_query(F.data == "pay_uah")
async def pay_uah(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state["product"]
    period = data_state["period"]
    product_name = PRODUCT_NAMES[product]
    price = PRICES[product][period]
    
    await state.update_data(uah_product=product, uah_period=period, uah_price=price, uah_product_name=product_name)
    
    text = f"""<tg-emoji emoji-id="5985596818912712352"> </tg-emoji> <b>Оплата гривной</b>

<tg-emoji emoji-id="5208513917965328345"> </tg-emoji> <b>Сумма:</b> {price} грн
<tg-emoji emoji-id="5877260593903177342"> </tg-emoji> <b>Товар:</b> {product_name} ({period})

<tg-emoji emoji-id="5208431570557360595"> </tg-emoji> <b>Карта для оплаты:</b> <code>{UAH_CARD}</code>
❗ <b>Комментарий:</b> <code>{UAH_COMMENT}</code>

<tg-emoji emoji-id="6050592962730005028"> </tg-emoji> <b>После оплаты отправьте скриншот чека сюда</b>

<tg-emoji emoji-id="5208431570557360595"> </tg-emoji> Без чека ключ НЕ будет выдан"""
    
    await callback.message.edit_text(text, reply_markup=uah_receipt_keyboard())
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
    
    text = "<tg-emoji emoji-id=\"5985596818912712352\"> </tg-emoji> Чек отправлен! Администратор выдаст ключ после проверки."
    await message.answer(text)
    await state.clear()

# ========== ПРОФИЛЬ И ПОКУПКИ ==========

@dp.callback_query(F.data == "menu_profile")
async def menu_profile(callback: types.CallbackQuery):
    user = data["users"][str(callback.from_user.id)]
    
    active = user.get("active_key") or "Нет активного ключа"
    product = user.get("active_product") or "—"
    expires = user.get("expires_at") or "—"
    
    text = f"""<tg-emoji emoji-id="5886412370347036129"> </tg-emoji> <b>Ваш профиль</b>

<tg-emoji emoji-id="5886505193180239900"> </tg-emoji> <b>ID:</b> <code>{user['user_id']}</code>
<tg-emoji emoji-id="5771887475421090729"> </tg-emoji> <b>Юзернейм:</b> @{user['username']}
<tg-emoji emoji-id="5897962422169243693"> </tg-emoji> <b>Имя:</b> {user['full_name']}

<tg-emoji emoji-id="6005570495603282482"> </tg-emoji> <b>Активный ключ:</b> <code>{active}</code>
<tg-emoji emoji-id="5208513917965328345"> </tg-emoji> <b>Товар:</b> {product}
<tg-emoji emoji-id="5897962422169243693"> </tg-emoji> <b>Срок до:</b> {expires}"""
    
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(is_admin(callback.from_user.id)))
    await callback.answer()

@dp.callback_query(F.data == "menu_purchases")
async def menu_purchases(callback: types.CallbackQuery):
    purchases = data["users"][str(callback.from_user.id)].get("purchases", [])
    
    if not purchases:
        text = "📭 <b>У вас пока нет покупок</b>\n\nИспользуйте Каталог для приобретения читов."
    else:
        text = "📜 <b>ИСТОРИЯ ПОКУПОК:</b>\n\n"
        for i, p in enumerate(reversed(purchases[-10:]), 1):
            status_emoji = "✅" if p['status'] == 'active' else "⏳"
            text += f"{i}. {status_emoji} <b>{p['product']}</b>\n"
            text += f"   Период: {p['period']}\n"
            text += f"   Цена: {p['price']} {p['currency']}\n"
            text += f"   Ключ: <code>{p['key']}</code>\n"
            text += f"   Дата: {p['purchased_at']}\n\n"
    
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(is_admin(callback.from_user.id)))
    await callback.answer()

# ========== АДМИН-ПАНЕЛЬ ==========

@dp.callback_query(F.data == "menu_admin")
async def menu_admin(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_uah = len(data["pending_uah"])
    pending_crypto = len([p for p in data["pending_crypto"] if p.startswith("crypto_")])
    
    text = f"🔧 <b>Админ-панель</b>\n\n📊 Ожидает подтверждения UAH: {pending_uah}\n💎 Ожидает подтверждения CRYPTO: {pending_crypto}\n\nВыберите действие:"
    await callback.message.edit_text(text, reply_markup=admin_panel_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "admin_give_key")
async def admin_give_key(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    text = "✏️ <b>Введите ID пользователя:</b>\n\n(можно найти в профиле пользователя)"
    await callback.message.edit_text(text, reply_markup=cancel_keyboard())
    await state.set_state(States.admin_waiting_user_id)
    await callback.answer()

@dp.callback_query(F.data == "admin_confirm_uah")
async def admin_confirm_uah(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    if not data["pending_uah"]:
        await callback.answer("Нет ожидающих UAH оплат!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for pid, info in data["pending_uah"].items():
        builder.button(text=f"✅ {info['username']} - {info['product']} ({info['price']} грн)", callback_data=f"confirm_uah_{pid}")
    builder.button(text="🔙 Назад", callback_data="menu_admin")
    builder.adjust(1)
    
    await callback.message.edit_text("📋 <b>Выберите UAH оплату для подтверждения:</b>", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "admin_confirm_crypto")
async def admin_confirm_crypto(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    crypto_pending = {k: v for k, v in data["pending_crypto"].items() if k.startswith("crypto_")}
    
    if not crypto_pending:
        await callback.answer("Нет ожидающих CRYPTO оплат!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for pid, info in crypto_pending.items():
        user = data["users"].get(str(info["user_id"]), {})
        username = user.get("username", "user")
        builder.button(text=f"💎 {username} - {info['product_name']} ({info['price']} USDT)", callback_data=f"confirm_crypto_{pid}")
    builder.button(text="🔙 Назад", callback_data="menu_admin")
    builder.adjust(1)
    
    await callback.message.edit_text("📋 <b>Выберите CRYPTO оплату для подтверждения:</b>", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_uah_"))
async def confirm_uah_payment(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_id = callback.data.replace("confirm_uah_", "")
    pending = data["pending_uah"].get(pending_id)
    
    if not pending:
        await callback.answer("Уже обработано!", show_alert=True)
        return
    
    await state.update_data(
        pending_id=pending_id, user_id=pending["user_id"], 
        product_name=pending["product"], period=pending["period"],
        price=pending["price"], product_code=pending["product_code"],
        period_code=pending["period_code"], payment_type="UAH"
    )
    
    text = f"✏️ <b>Введите ключ для пользователя @{pending['username']}</b>\n\nТовар: {pending['product']} ({pending['period']})"
    await callback.message.edit_text(text, reply_markup=cancel_keyboard())
    await state.set_state(States.admin_waiting_uah_key)
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_crypto_"))
async def confirm_crypto_payment(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_id = callback.data.replace("confirm_crypto_", "")
    pending = data["pending_crypto"].get(pending_id)
    
    if not pending:
        await callback.answer("Уже обработано!", show_alert=True)
        return
    
    user = data["users"].get(str(pending["user_id"]), {})
    
    await state.update_data(
        pending_id=pending_id, user_id=pending["user_id"], 
        product_name=pending["product_name"], period=pending["period"],
        price=pending["price"], product_code=pending["product"],
        period_code=pending["period"], payment_type="CRYPTO"
    )
    
    text = f"✏️ <b>Введите ключ для пользователя @{user.get('username', 'user')}</b>\n\nТовар: {pending['product_name']} ({pending['period']})"
    await callback.message.edit_text(text, reply_markup=cancel_keyboard())
    await state.set_state(States.admin_waiting_crypto_key)
    await callback.answer()

@dp.message(States.admin_waiting_user_id)
async def get_user_id_for_key(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        if str(user_id) not in data["users"]:
            await message.answer("❌ Пользователь не найден!")
            await state.clear()
            await show_main_menu(message.chat.id)
            return
        await state.update_data(target_user=user_id)
        text = "🔑 <b>Введите ключ для выдачи:</b>"
        await message.answer(text, reply_markup=cancel_keyboard())
        await state.set_state(States.admin_waiting_key)
    except:
        await message.answer("❌ Введите корректный ID (число)!")

@dp.message(States.admin_waiting_key)
async def send_key_to_user(message: types.Message, state: FSMContext):
    key = message.text
    data_state = await state.get_data()
    user_id = data_state["target_user"]
    
    data["users"][str(user_id)]["active_key"] = key
    data["users"][str(user_id)]["active_product"] = "Выдан администратором"
    data["users"][str(user_id)]["expires_at"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    save_data()
    
    await bot.send_message(user_id, f"✅ <b>Вам выдан ключ администратором!</b>\n\n🔑 Ключ: <code>{key}</code>\n\nИспользуйте его для активации.", parse_mode="HTML")
    await message.answer(f"✅ Ключ отправлен пользователю {user_id}!")
    await state.clear()
    await show_main_menu(message.chat.id)

@dp.message(States.admin_waiting_uah_key)
async def send_uah_key(message: types.Message, state: FSMContext):
    key = message.text
    data_state = await state.get_data()
    
    pending_id = data_state["pending_id"]
    user_id = data_state["user_id"]
    product_name = data_state["product_name"]
    period = data_state["period"]
    price = data_state["price"]
    
    add_purchase(user_id, product_name, period, price, "UAH", key, status="active")
    activate_key(user_id, key, product_name, period)
    
    if pending_id in data["pending_uah"]:
        del data["pending_uah"][pending_id]
    save_data()
    
    text = f"""<tg-emoji emoji-id="5985596818912712352"> </tg-emoji> <b>Ваша UAH оплата подтверждена!</b>

<tg-emoji emoji-id="5208513917965328345"> </tg-emoji> <b>Товар:</b> {product_name} ({period})
<tg-emoji emoji-id="6005570495603282482"> </tg-emoji> <b>Ваш ключ:</b> <code>{key}</code>

<tg-emoji emoji-id="5985596818912712352"> </tg-emoji> Спасибо за покупку!"""
    
    await bot.send_message(user_id, text, parse_mode="HTML")
    await message.answer(f"✅ Ключ выдан пользователю {user_id}!\n\nТовар: {product_name} ({period})")
    await state.clear()
    await show_main_menu(message.chat.id)

@dp.message(States.admin_waiting_crypto_key)
async def send_crypto_key(message: types.Message, state: FSMContext):
    key = message.text
    data_state = await state.get_data()
    
    pending_id = data_state["pending_id"]
    user_id = data_state["user_id"]
    product_name = data_state["product_name"]
    period = data_state["period"]
    price = data_state["price"]
    
    add_purchase(user_id, product_name, period, price, "USDT", key, status="active")
    activate_key(user_id, key, product_name, period)
    
    if pending_id in data["pending_crypto"]:
        del data["pending_crypto"][pending_id]
    save_data()
    
    text = f"""<tg-emoji emoji-id="5985596818912712352"> </tg-emoji> <b>Ваша CRYPTO оплата подтверждена!</b>

<tg-emoji emoji-id="5208513917965328345"> </tg-emoji> <b>Товар:</b> {product_name} ({period})
<tg-emoji emoji-id="6005570495603282482"> </tg-emoji> <b>Ваш ключ:</b> <code>{key}</code>

<tg-emoji emoji-id="5985596818912712352"> </tg-emoji> Спасибо за покупку!"""
    
    await bot.send_message(user_id, text, parse_mode="HTML")
    await message.answer(f"✅ Ключ выдан пользователю {user_id}!\n\nТовар: {product_name} ({period})")
    await state.clear()
    await show_main_menu(message.chat.id)

# ========== НАВИГАЦИЯ ==========

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback.message.chat.id)
    await callback.answer()

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "<tg-emoji emoji-id=\"5960551395730919906\"> </tg-emoji> <b>Выберите игру:</b>"
    await send_with_emoji(callback.message.chat.id, text, catalog_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_products")
async def back_to_products(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    game = data_state.get("game", "oxide")
    text = f"<tg-emoji emoji-id=\"5819078828017849357\"> </tg-emoji> <b>{'Oxide Survival Island' if game == 'oxide' else 'Standoff 2'} - Выберите софт:</b>"
    await send_with_emoji(callback.message.chat.id, text, products_keyboard(game))
    await callback.answer()

@dp.callback_query(F.data == "back_to_periods")
async def back_to_periods(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state["product"]
    product_name = PRODUCT_NAMES[product]
    text = f"<tg-emoji emoji-id=\"5877260593903177342\"> </tg-emoji> <b>{product_name}</b>\n\nВыберите период:"
    await send_with_emoji(callback.message.chat.id, text, periods_keyboard(product))
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
