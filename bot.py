import asyncio
import json
import os
import hashlib
import hmac
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict
import random
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== КОНФИГ ==========
BOT_TOKEN = "8743517612:AAFrgMXZpRnDQclyuiRYNKSziV-TPhkB_S8"
ADMIN_ID = 7496589494
CRYPTO_BOT_TOKEN = "560372:AAyQpvWZFSHpzrnVAhVwPF7PbcJmqI7bH0K"
UAH_CARD = "4441111008011946"
UAH_COMMENT = "За цифрові товари"

# Фото
MENU_PHOTO = "https://files.catbox.moe/vz52pd.png"
CATALOG_PHOTO = "https://files.catbox.moe/w1ruj1.png"
GAME_SELECT_PHOTO = "https://files.catbox.moe/kxk5w3.png"
SYSTEM_PHOTO = "https://files.catbox.moe/87qpck.png"
PERIOD_PHOTO = "https://files.catbox.moe/b795ua.png"
PAYMENT_PHOTO = "https://files.catbox.moe/tzogel.png"

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
    # Каталог
    selecting_game = State()
    selecting_product = State()
    selecting_period = State()
    selecting_payment = State()
    # UAH оплата
    waiting_uah_receipt = State()
    # Крипто оплата
    waiting_crypto_payment = State()
    # Админ
    admin_waiting_user_id = State()
    admin_waiting_key = State()
    admin_waiting_crypto_key = State()
    admin_waiting_uah_key = State()

# ========== КЛАВИАТУРЫ ==========

def agreement_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я ознакомлен с правилами", callback_data="agree")]
    ])

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍 Каталог", callback_data="menu_catalog")
    builder.button(text="👤 Профиль", callback_data="menu_profile")
    builder.button(text="📦 Мои покупки", callback_data="menu_purchases")
    builder.button(text="🔧 Админ-панель", callback_data="menu_admin")
    builder.adjust(1)
    return builder.as_markup()

def admin_panel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Выдать ключ пользователю", callback_data="admin_give_key")
    builder.button(text="💰 Подтвердить UAH оплату", callback_data="admin_confirm_uah")
    builder.button(text="💎 Подтвердить CRYPTO оплату", callback_data="admin_confirm_crypto")
    builder.button(text="🔙 В главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

def catalog_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Oxide Survival Island", callback_data="game_oxide")
    builder.button(text="💥 Standoff 2", callback_data="game_standoff")
    builder.button(text="🔙 В главное меню", callback_data="back_to_main")
    builder.adjust(1)
    return builder.as_markup()

def products_keyboard(game):
    builder = InlineKeyboardBuilder()
    if game == "oxide":
        builder.button(text="Lebro [VIP]", callback_data="product_Lebro_VIP")
        builder.button(text="Lebro [Lite]", callback_data="product_Lebro_Lite")
    else:
        builder.button(text="Plutonium", callback_data="product_Plutonium")
    builder.button(text="🔙 Назад к играм", callback_data="back_to_catalog")
    builder.adjust(1)
    return builder.as_markup()

def periods_keyboard(product):
    builder = InlineKeyboardBuilder()
    for name, code in PERIODS[product]:
        builder.button(text=name, callback_data=f"period_{code}")
    builder.button(text="🔙 Назад к продуктам", callback_data="back_to_products")
    builder.adjust(1)
    return builder.as_markup()

def payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="💸 CryptoPay (USDT)", callback_data="pay_crypto")
    builder.button(text="🇺🇦 Оплата гривной", callback_data="pay_uah")
    builder.button(text="🔙 Назад к периодам", callback_data="back_to_periods")
    builder.adjust(1)
    return builder.as_markup()

def check_payment_keyboard(invoice_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_payment_{invoice_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")]
    ])

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

# ========== CRYPTOPAY API ==========

class CryptoPayAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://pay.crypt.bot/api"
    
    async def create_invoice(self, amount: float, currency: str = "USDT", description: str = "") -> Optional[Dict]:
        """Создание счета в CryptoPay"""
        url = f"{self.base_url}/createInvoice"
        params = {
            "asset": currency,
            "amount": str(amount),
            "description": description[:100]
        }
        headers = {
            "Crypto-Pay-API-Token": self.token
        }
        
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
        """Проверка статуса счета"""
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
    """Активация ключа для пользователя"""
    data["users"][str(user_id)]["active_key"] = key
    data["users"][str(user_id)]["active_product"] = product_name
    
    days = 1 if period == "24h" else int(period.replace("d", ""))
    expires = datetime.now() + timedelta(days=days)
    data["users"][str(user_id)]["expires_at"] = expires.strftime("%Y-%m-%d %H:%M:%S")
    
    # Обновляем последнюю покупку
    for purchase in reversed(data["users"][str(user_id)]["purchases"]):
        if purchase["product"] == product_name and purchase["period"] == period and purchase["status"] == "pending":
            purchase["status"] = "active"
            purchase["key"] = key
            break
    
    save_data()

# ========== БОТ ==========

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

async def send_with_photo(chat_id, photo_url, caption, keyboard=None):
    await bot.send_photo(
        chat_id=chat_id,
        photo=photo_url,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ========== ОСНОВНЫЕ ХЭНДЛЕРЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    register_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    if not data["users"][str(message.from_user.id)]["agreed"]:
        rules = """📜 *Правила PlayCheatGameBot* 

🚫 *1. Возврат:* Возврата нет — при покупке цифрового товара потеря, неправильное использование никто не компенсирует.

⚠️ *2. Ответственность:* Исполнитель не несёт ответственности за последствия применения.

📜 *3. Общие:* Оплачивая услугу, вы соглашаетесь с данными правилами.

🛡 *4. Заключительные:* Исполнитель вправе изменять условия.

✅ Нажмите на кнопку ниже, чтобы продолжить"""
        await message.answer(rules, parse_mode="Markdown", reply_markup=agreement_keyboard())
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
    text = """🛡 *PlayCheatGameBot* - Надёжный магазин читов

✅ *Почему мы?*
• Моментальная выдача после оплаты
• Работает на всех устройствах (NO ROOT)
• Анонимная оплата криптовалютой
• 24/7 поддержка
• Проверенные софты

*Выберите действие:*"""
    await send_with_photo(chat_id, MENU_PHOTO, text, main_menu_keyboard())

# КАТАЛОГ
@dp.callback_query(F.data == "menu_catalog")
async def menu_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "📋 *Выберите игру:*"
    await send_with_photo(callback.message.chat.id, CATALOG_PHOTO, text, catalog_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "game_oxide")
async def game_oxide(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(game="oxide")
    text = "🎮 *Oxide Survival Island - Выберите софт:*"
    await send_with_photo(callback.message.chat.id, GAME_SELECT_PHOTO, text, products_keyboard("oxide"))
    await callback.answer()

@dp.callback_query(F.data == "game_standoff")
async def game_standoff(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(game="standoff")
    text = "🎮 *Standoff 2 - Выберите софт:*"
    await send_with_photo(callback.message.chat.id, GAME_SELECT_PHOTO, text, products_keyboard("standoff"))
    await callback.answer()

@dp.callback_query(F.data.startswith("product_"))
async def select_product(callback: types.CallbackQuery, state: FSMContext):
    product = callback.data.replace("product_", "")
    await state.update_data(product=product)
    product_name = PRODUCT_NAMES[product]
    text = f"📦 *{product_name}*\n\nВыберите период действия:"
    await send_with_photo(callback.message.chat.id, SYSTEM_PHOTO, text, periods_keyboard(product))
    await callback.answer()

@dp.callback_query(F.data.startswith("period_"))
async def select_period(callback: types.CallbackQuery, state: FSMContext):
    period = callback.data.replace("period_", "")
    await state.update_data(period=period)
    
    data_state = await state.get_data()
    product = data_state["product"]
    price = PRICES[product][period]
    currency = "USDT" if "Lebro" in product else "UAH"
    
    text = f"""💸 *К оплате:* {price} {currency}

Выберите способ оплаты:"""
    await send_with_photo(callback.message.chat.id, PAYMENT_PHOTO, text, payment_keyboard())
    await callback.answer()

# ========== CRYPTO ОПЛАТА ==========

@dp.callback_query(F.data == "pay_crypto")
async def pay_crypto(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state["product"]
    period = data_state["period"]
    product_name = PRODUCT_NAMES[product]
    price = PRICES[product][period]
    
    # Создаем инвойс в CryptoPay
    invoice = await crypto_api.create_invoice(price, "USDT", f"{product_name} {period}")
    
    if not invoice:
        await callback.message.edit_caption(
            caption="❌ Ошибка создания счета. Попробуйте позже.",
            reply_markup=payment_keyboard()
        )
        await callback.answer()
        return
    
    invoice_id = invoice["invoice_id"]
    pay_url = invoice["pay_url"]
    
    # Сохраняем информацию
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
    
    text = f"""💸 *Создан счет на оплату*

💰 Сумма: {price} USDT
📦 Товар: {product_name} ({period})

🔗 *Ссылка для оплаты:* [Оплатить]({pay_url})

🔄 После оплаты нажмите кнопку ниже для проверки"""
    
    await callback.message.edit_caption(
        caption=text, 
        parse_mode="Markdown",
        reply_markup=check_payment_keyboard(invoice_id)
    )
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
    
    # Проверяем статус
    invoice = await crypto_api.check_invoice(invoice_id)
    
    if not invoice:
        await callback.answer("❌ Ошибка проверки", show_alert=True)
        return
    
    status = invoice.get("status")
    
    if status == "paid":
        # Оплата прошла, отправляем админу на подтверждение
        user_id = invoice_info["user_id"]
        
        # Добавляем в pending на выдачу ключа
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
        
        text = f"""✅ *Оплата подтверждена!*

💰 Сумма: {invoice_info['price']} USDT оплачена
📦 Товар: {invoice_info['product_name']} ({invoice_info['period']})

⏳ Ожидайте выдачи ключа от администратора...
Администратор уже уведомлен."""
        
        await callback.message.edit_caption(caption=text, parse_mode="Markdown")
        
        # Уведомляем админа
        await bot.send_message(
            ADMIN_ID,
            f"🔔 *НОВАЯ CRYPTO ОПЛАТА*\n\n"
            f"👤 Пользователь: @{callback.from_user.username or 'Нет'} (ID: {user_id})\n"
            f"📦 Товар: {invoice_info['product_name']} ({invoice_info['period']})\n"
            f"💰 Сумма: {invoice_info['price']} USDT\n"
            f"🆔 Invoice: {invoice_id}\n\n"
            f"Используйте *Админ-панель → Подтвердить CRYPTO оплату* для выдачи ключа",
            parse_mode="Markdown"
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
    
    text = f"""🇺🇦 *Оплата гривной*

💰 Сумма: {price} грн
📦 Товар: {product_name} ({period})

💳 *Карта для оплаты:* `{UAH_CARD}`
❗ *Комментарий:* `{UAH_COMMENT}`

📸 *После оплаты отправьте скриншот чека сюда*

❗ Без чека ключ НЕ будет выдан"""
    
    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=cancel_keyboard())
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
    
    admin_text = f"""🔔 *НОВАЯ ОПЛАТА UAH*

👤 Пользователь: @{message.from_user.username or 'Нет'} (ID: {user_id})
📦 Товар: {data_state['uah_product_name']} ({data_state['uah_period']})
💰 Сумма: {data_state['uah_price']} грн

🆔 ID чека: `{pending_id}`

Используйте *Админ-панель → Подтвердить UAH оплату* для выдачи"""
    
    await bot.send_photo(ADMIN_ID, photo_id, caption=admin_text, parse_mode="Markdown")
    await message.answer("✅ Чек отправлен! Администратор выдаст ключ после проверки.")
    await state.clear()

# ========== ПРОФИЛЬ И ПОКУПКИ ==========

@dp.callback_query(F.data == "menu_profile")
async def menu_profile(callback: types.CallbackQuery):
    user = data["users"][str(callback.from_user.id)]
    
    active = user.get("active_key") or "Нет активного ключа"
    product = user.get("active_product") or "—"
    expires = user.get("expires_at") or "—"
    
    text = f"""👤 *Ваш профиль*

🆔 ID: `{user['user_id']}`
📛 Юзернейм: @{user['username']}
👤 Имя: {user['full_name']}

🔑 *Активный ключ:* `{active}`
📦 *Товар:* {product}
⏳ *Срок до:* {expires}"""
    
    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "menu_purchases")
async def menu_purchases(callback: types.CallbackQuery):
    purchases = data["users"][str(callback.from_user.id)].get("purchases", [])
    
    if not purchases:
        text = "📭 *У вас пока нет покупок*\n\nИспользуйте Каталог для приобретения читов."
    else:
        text = "📜 *ИСТОРИЯ ПОКУПОК:*\n\n"
        for i, p in enumerate(reversed(purchases[-10:]), 1):
            status_emoji = "✅" if p['status'] == 'active' else "⏳"
            text += f"{i}. {status_emoji} *{p['product']}*\n"
            text += f"   Период: {p['period']}\n"
            text += f"   Цена: {p['price']} {p['currency']}\n"
            text += f"   Ключ: `{p['key']}`\n"
            text += f"   Дата: {p['purchased_at']}\n\n"
    
    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    await callback.answer()

# ========== АДМИН-ПАНЕЛЬ ==========

@dp.callback_query(F.data == "menu_admin")
async def menu_admin(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_uah = len(data["pending_uah"])
    pending_crypto = len([p for p in data["pending_crypto"] if p.startswith("crypto_")])
    
    text = f"🔧 *Админ-панель*\n\n📊 Ожидает подтверждения UAH: {pending_uah}\n💎 Ожидает подтверждения CRYPTO: {pending_crypto}\n\nВыберите действие:"
    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=admin_panel_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "admin_give_key")
async def admin_give_key(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    await callback.message.edit_caption(caption="✏️ *Введите ID пользователя:*\n\n(можно найти в профиле пользователя)", 
                                        parse_mode="Markdown", reply_markup=cancel_keyboard())
    await state.set_state(States.admin_waiting_user_id)
    await callback.answer()

# Подтверждение UAH
@dp.callback_query(F.data == "admin_confirm_uah")
async def admin_confirm_uah(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    if not data["pending_uah"]:
        await callback.answer("Нет ожидающих UAH оплат!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for pid, info in data["pending_uah"].items():
        builder.button(text=f"✅ @{info['username']} - {info['product']} ({info['price']} грн)", callback_data=f"confirm_uah_{pid}")
    builder.button(text="🔙 Назад", callback_data="menu_admin")
    builder.adjust(1)
    
    await callback.message.edit_caption(caption="📋 *Выберите UAH оплату для подтверждения:*", 
                                        parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_uah_"))
async def confirm_uah_payment(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_id = callback.data.replace("confirm_uah_", "")
    pending = data["pending_uah"].get(pending_id)
    
    if not pending:
        await callback.answer("Уже обработано!", show_alert=True)
        return
    
    await state.update_data(pending_id=pending_id, user_id=pending["user_id"], 
                          product_name=pending["product"], period=pending["period"],
                          price=pending["price"], product_code=pending["product_code"],
                          period_code=pending["period_code"], payment_type="UAH")
    
    await callback.message.edit_caption(caption=f"✏️ *Введите ключ для пользователя @{pending['username']}*\n\nТовар: {pending['product']} ({pending['period']})",
                                        parse_mode="Markdown", reply_markup=cancel_keyboard())
    await state.set_state(States.admin_waiting_uah_key)
    await callback.answer()

# Подтверждение CRYPTO
@dp.callback_query(F.data == "admin_confirm_crypto")
async def admin_confirm_crypto(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    crypto_pending = {k: v for k, v in data["pending_crypto"].items() if k.startswith("crypto_")}
    
    if not crypto_pending:
        await callback.answer("Нет ожидающих CRYPTO оплат!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for pid, info in crypto_pending.items():
        builder.button(text=f"💎 @{info.get('username', 'user')} - {info['product_name']} ({info['price']} USDT)", callback_data=f"confirm_crypto_{pid}")
    builder.button(text="🔙 Назад", callback_data="menu_admin")
    builder.adjust(1)
    
    # Получаем username для отображения
    for pid, info in crypto_pending.items():
        user = data["users"].get(str(info["user_id"]), {})
        info["username"] = user.get("username", "user")
    
    await callback.message.edit_caption(caption="📋 *Выберите CRYPTO оплату для подтверждения:*", 
                                        parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_crypto_"))
async def confirm_crypto_payment(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_id = callback.data.replace("confirm_crypto_", "")
    pending = data["pending_crypto"].get(pending_id)
    
    if not pending:
        await callback.answer("Уже обработано!", show_alert=True)
        return
    
    await state.update_data(pending_id=pending_id, user_id=pending["user_id"], 
                          product_name=pending["product_name"], period=pending["period"],
                          price=pending["price"], product_code=pending["product"],
                          period_code=pending["period"], payment_type="CRYPTO")
    
    await callback.message.edit_caption(caption=f"✏️ *Введите ключ для пользователя ID: {pending['user_id']}*\n\nТовар: {pending['product_name']} ({pending['period']})",
                                        parse_mode="Markdown", reply_markup=cancel_keyboard())
    await state.set_state(States.admin_waiting_crypto_key)
    await callback.answer()

# Выдача ключей (общий обработчик)
@dp.message(States.admin_waiting_user_id)
async def get_user_id_for_key(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        if str(user_id) not in data["users"]:
            await message.answer("❌ Пользователь не найден!", reply_markup=main_menu_keyboard())
            await state.clear()
            return
        await state.update_data(target_user=user_id)
        await message.answer("🔑 *Введите ключ для выдачи:*", parse_mode="Markdown", reply_markup=cancel_keyboard())
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
    
    await bot.send_message(user_id, f"✅ *Вам выдан ключ администратором!*\n\n🔑 Ключ: `{key}`\n\nИспользуйте его для активации.", parse_mode="Markdown")
    await message.answer(f"✅ Ключ отправлен пользователю {user_id}!", reply_markup=main_menu_keyboard())
    await state.clear()

@dp.message(States.admin_waiting_uah_key)
async def send_uah_key(message: types.Message, state: FSMContext):
    key = message.text
    data_state = await state.get_data()
    
    pending_id = data_state["pending_id"]
    user_id = data_state["user_id"]
    product_name = data_state["product_name"]
    period = data_state["period"]
    price = data_state["price"]
    product_code = data_state["product_code"]
    period_code = data_state["period_code"]
    
    # Добавляем покупку и активируем
    add_purchase(user_id, product_name, period, price, "UAH", key, status="active")
    activate_key(user_id, key, product_name, period)
    
    # Удаляем из pending
    if pending_id in data["pending_uah"]:
        del data["pending_uah"][pending_id]
    save_data()
    
    await bot.send_message(user_id, f"✅ *Ваша UAH оплата подтверждена!*\n\n📦 Товар: {product_name} ({period})\n🔑 *Ваш ключ:* `{key}`\n\nСпасибо за покупку!", parse_mode="Markdown")
    await message.answer(f"✅ Ключ выдан пользователю {user_id}!\n\nТовар: {product_name} ({period})", reply_markup=main_menu_keyboard())
    await state.clear()

@dp.message(States.admin_waiting_crypto_key)
async def send_crypto_key(message: types.Message, state: FSMContext):
    key = message.text
    data_state = await state.get_data()
    
    pending_id = data_state["pending_id"]
    user_id = data_state["user_id"]
    product_name = data_state["product_name"]
    period = data_state["period"]
    price = data_state["price"]
    product_code = data_state["product_code"]
    period_code = data_state["period_code"]
    
    # Добавляем покупку и активируем
    add_purchase(user_id, product_name, period, price, "USDT", key, status="active")
    activate_key(user_id, key, product_name, period)
    
    # Удаляем из pending
    if pending_id in data["pending_crypto"]:
        del data["pending_crypto"][pending_id]
    save_data()
    
    await bot.send_message(user_id, f"✅ *Ваша CRYPTO оплата подтверждена!*\n\n📦 Товар: {product_name} ({period})\n🔑 *Ваш ключ:* `{key}`\n\nСпасибо за покупку!", parse_mode="Markdown")
    await message.answer(f"✅ Ключ выдан пользователю {user_id}!\n\nТовар: {product_name} ({period})", reply_markup=main_menu_keyboard())
    await state.clear()

# ========== НАВИГАЦИЯ ==========

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback.message.chat.id)
    await callback.answer()

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = "📋 *Выберите игру:*"
    await send_with_photo(callback.message.chat.id, CATALOG_PHOTO, text, catalog_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "back_to_products")
async def back_to_products(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    game = data_state.get("game", "oxide")
    text = "🎮 *Выберите софт:*"
    await send_with_photo(callback.message.chat.id, GAME_SELECT_PHOTO, text, products_keyboard(game))
    await callback.answer()

@dp.callback_query(F.data == "back_to_periods")
async def back_to_periods(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state["product"]
    product_name = PRODUCT_NAMES[product]
    text = f"📦 *{product_name}*\n\nВыберите период:"
    await send_with_photo(callback.message.chat.id, PERIOD_PHOTO, text, periods_keyboard(product))
    await callback.answer()

@dp.callback_query(F.data == "cancel")
async def cancel_action(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await show_main_menu(callback.message.chat.id)
    await callback.answer()

# ========== ЗАПУСК ==========

async def main():
    print("✅ Бот запущен!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("📦 Жду команды...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
