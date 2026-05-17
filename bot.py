from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio

BOT_TOKEN = "8614807346:AAFhTgIEGVEIj3q2UTOxkeIIvBisn47TUdc"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    text = 'Привет, Салфетка и Хабр! <tg-emoji emoji-id="5285430309720966085">👍</tg-emoji>'
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="Опасная кнопка!",
                callback_data="btn1"
            ),
            types.InlineKeyboardButton(
                text="Успешная кпнока =)",
                callback_data="btn2"
            )
        ],
        [
            types.InlineKeyboardButton(
                text="Основная кнопка",
                callback_data="btn3"
            ),
            types.InlineKeyboardButton(
                text="Простокнопка -_-",
                callback_data="btn4"
            )
        ]
    ])
    
    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@dp.callback_query()
async def handle_buttons(callback: types.CallbackQuery):
    await callback.answer(f"Ты нажал: {callback.data}")
    await callback.message.answer(f"✅ Нажата кнопка: {callback.data}")

async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
