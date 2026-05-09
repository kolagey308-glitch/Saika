import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
import random

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== КОНФИГ ==========
BOT_TOKEN = "8743517612:AAFrgMXZpRnDQclyuiRYNKSziV-TPhkB_S8"
ADMIN_ID = 7496589494
CRYPTO_BOT_TOKEN = "560372:AAyQpvWZFSHpzrnVAhVwPF7PbcJmqI7bH0K"
UAH_CARD = "4441111008011946"
UAH_COMMENT = "За цифрові товари"

# Фото для меню
MENU_PHOTO = "https://files.catbox.moe/vz52pd.png"
CATALOG_PHOTO = "https://files.catbox.moe/w1ruj1.png"
GAME_SELECT_PHOTO = "https://files.catbox.moe/kxk5w3.png"
SYSTEM_PHOTO = "https://files.catbox.moe/87qpck.png"
PERIOD_PHOTO = "https://files.catbox.moe/b795ua.png"
PAYMENT_PHOTO = "https://files.catbox.moe/tzogel.png"

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
    return {"users": {}, "pending_uah": {}, "temp_keys": {}}

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
    admin_waiting_user_id = State()
    admin_waiting_key = State()
    admin_waiting_manual_key = State()

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
    if is_admin:
        builder.button(text="🔧 Админ-панель", callback_data="menu_admin")
    builder.adjust(1)
    return builder.as_markup()

def admin_panel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔑 Выдать ключ пользователю", callback_data="admin_give_key")
    builder.button(text="💰 Подтвердить UAH оплату", callback_data="admin_confirm_uah")
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
        builder.button(text="Lebro [VIP] (VIP доступ)", callback_data="product_Lebro_VIP")
        builder.button(text="Lebro [Lite] (Лайт доступ)", callback_data="product_Lebro_Lite")
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
    builder.button(text="💸 CryptoPay (USDT - авто)", callback_data="pay_crypto")
    builder.button(text="🇺🇦 Оплата гривной (карта)", callback_data="pay_uah")
    builder.button(text="🔙 Назад к периодам", callback_data="back_to_periods")
    builder.adjust(1)
    return builder.as_markup()

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

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

def add_purchase(user_id, product_name, period, price, currency, key, status="active"):
    purchase = {
        "product": product_name,
        "period": period,
        "price": price,
        "currency": currency,
        "key": key,
        "purchased_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status
    }
    data["users"][str(user_id)]["purchases"].append(purchase)
    
    if status == "active":
        data["users"][str(user_id)]["active_key"] = key
        data["users"][str(user_id)]["active_product"] = product_name
        
        days = 0
        if period == "24h":
            days = 1
        elif period == "7d":
            days = 7
        elif period == "30d":
            days = 30
        elif period == "90d":
            days = 90
        
        expires = datetime.now() + timedelta(days=days)
        data["users"][str(user_id)]["expires_at"] = expires.strftime("%Y-%m-%d %H:%M:%S")
    
    save_data()

def generate_demo_key():
    return f"DEMO-{random.randint(100000, 999999)}"

# ========== БОТ ==========

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Глобальная проверка админа
is_admin = False

async def send_with_photo(chat_id, photo_url, caption, keyboard=None):
    """Отправка сообщения с фото"""
    await bot.send_photo(
        chat_id=chat_id,
        photo=photo_url,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ========== ХЭНДЛЕРЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    global is_admin
    is_admin = (message.from_user.id == ADMIN_ID)
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

# Каталог
@dp.callback_query(F.data == "menu_catalog")
async def menu_catalog(callback: types.CallbackQuery, state: FSMContext):
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

@dp.callback_query(F.data == "pay_crypto")
async def pay_crypto(callback: types.CallbackQuery, state: FSMContext):
    data_state = await state.get_data()
    product = data_state["product"]
    period = data_state["period"]
    product_name = PRODUCT_NAMES[product]
    price = PRICES[product][period]
    
    # Демо-симуляция автовыдачи
    demo_key = generate_demo_key()
    
    # Добавляем покупку
    add_purchase(callback.from_user.id, product_name, period, price, "USDT", demo_key)
    
    text = f"""✅ *Оплата прошла успешно!*

📦 Товар: {product_name}
⏱ Период: {period}
🔑 *Ваш ключ:* `{demo_key}`

❗ В демо-режиме ключ выдан автоматически.
В реальном режиме CryptoPay выдаст ключ после подтверждения оплаты."""
    
    await callback.message.edit_caption(caption=text, parse_mode="Markdown")
    await callback.answer("✅ Ключ выдан!", show_alert=True)
    await state.clear()

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
    
    pending_id = f"{user_id}_{int(datetime.now().timestamp())}"
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
    
    # Уведомление админу
    admin_text = f"""🔔 *НОВАЯ ОПЛАТА UAH*

👤 Пользователь: @{message.from_user.username or 'Нет'} (ID: {user_id})
📦 Товар: {data_state['uah_product_name']} ({data_state['uah_period']})
💰 Сумма: {data_state['uah_price']} грн

🆔 ID чека: `{pending_id}`

Используйте *Админ-панель → Подтвердить UAH оплату* для выдачи"""
    
    await bot.send_photo(ADMIN_ID, photo_id, caption=admin_text, parse_mode="Markdown")
    await message.answer("✅ Чек отправлен! Администратор выдаст ключ после проверки.")
    await state.clear()

# Профиль
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
⏳ *Срок до:* {expires}

Используйте ключ в приложении для активации."""
    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    await callback.answer()

# Мои покупки
@dp.callback_query(F.data == "menu_purchases")
async def menu_purchases(callback: types.CallbackQuery):
    purchases = data["users"][str(callback.from_user.id)].get("purchases", [])
    
    if not purchases:
        text = "📭 *У вас пока нет покупок*\n\nИспользуйте Каталог для приобретения читов."
    else:
        text = "📜 *ИСТОРИЯ ПОКУПОК:*\n\n"
        for i, p in enumerate(reversed(purchases[-5:]), 1):
            text += f"{i}. *{p['product']}*\n"
            text += f"   Период: {p['period']}\n"
            text += f"   Цена: {p['price']} {p['currency']}\n"
            text += f"   Ключ: `{p['key']}`\n"
            text += f"   Дата: {p['purchased_at']}\n\n"
    
    await callback.message.edit_caption(caption=text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    await callback.answer()

# Админ-панель
@dp.callback_query(F.data == "menu_admin")
async def menu_admin(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_count = len(data["pending_uah"])
    text = f"🔧 *Админ-панель*\n\n📊 Ожидает подтверждения UAH: {pending_count}\n\nВыберите действие:"
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

@dp.callback_query(F.data == "admin_confirm_uah")
async def admin_confirm_uah(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    if not data["pending_uah"]:
        await callback.answer("Нет ожидающих оплат!", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    for pid, info in data["pending_uah"].items():
        builder.button(text=f"✅ @{info['username']} - {info['product']}", callback_data=f"confirm_{pid}")
    builder.button(text="🔙 Назад", callback_data="menu_admin")
    builder.adjust(1)
    
    await callback.message.edit_caption(caption="📋 *Выберите оплату для подтверждения:*", 
                                        parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_"))
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен", show_alert=True)
        return
    
    pending_id = callback.data.replace("confirm_", "")
    pending = data["pending_uah"].get(pending_id)
    
    if not pending:
        await callback.answer("Уже обработано!", show_alert=True)
        return
    
    await state.update_data(pending_id=pending_id, user_id=pending["user_id"], 
                          product=pending["product"], period=pending["period"],
                          price=pending["price"], product_code=pending["product_code"],
                          period_code=pending["period_code"])
    
    await callback.message.edit_caption(caption=f"✏️ *Введите ключ для пользователя @{pending['username']}*\n\nТовар: {pending['product']} ({pending['period']})",
                                        parse_mode="Markdown", reply_markup=cancel_keyboard())
    await state.set_state(States.admin_waiting_manual_key)
    await callback.answer()

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
    
    # Выдаем ключ (демо-ключ без конкретного товара)
    data["users"][str(user_id)]["active_key"] = key
    data["users"][str(user_id)]["active_product"] = "Выдан администратором"
    data["users"][str(user_id)]["expires_at"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    save_data()
    
    await bot.send_message(user_id, f"✅ *Вам выдан ключ администратором!*\n\n🔑 Ключ: `{key}`\n\nИспользуйте его для активации.", parse_mode="Markdown")
    await message.answer(f"✅ Ключ отправлен пользователю {user_id}!", reply_markup=main_menu_keyboard())
    await state.clear()

@dp.message(States.admin_waiting_manual_key)
async def send_manual_key(message: types.Message, state: FSMContext):
    key = message.text
    data_state = await state.get_data()
    
    pending_id = data_state["pending_id"]
    user_id = data_state["user_id"]
    product_name = data_state["product"]
    period = data_state["period"]
    price = data_state["price"]
    product_code = data_state["product_code"]
    period_code = data_state["period_code"]
    
    # Добавляем покупку
    add_purchase(user_id, product_name, period, price, "UAH", key)
    
    # Удаляем из pending
    del data["pending_uah"][pending_id]
    save_data()
    
    await bot.send_message(user_id, f"✅ *Ваша оплата подтверждена!*\n\n📦 Товар: {product_name} ({period})\n🔑 *Ваш ключ:* `{key}`\n\nСпасибо за покупку!", parse_mode="Markdown")
    await message.answer(f"✅ Ключ выдан пользователю {user_id}!\n\nТовар: {product_name} ({period})", reply_markup=main_menu_keyboard())
    await state.clear()

# Навигация
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await show_main_menu(callback.message.chat.id)
    await callback.answer()

@dp.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback: types.CallbackQuery):
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

async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
