from aiogram import Bot, Dispatcher, executor, types
import logging
import json

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8585841930:AAFuPSIdTLnVFJFxJMWnapIZoWWyGvhNFTs"
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# ▶️ /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton(
            text="🍽 Открыть меню",
            web_app=types.WebAppInfo(url=WEBAPP_URL)
        )
    )

    await message.answer(
        "Добро пожаловать 👋\nОткройте меню:",
        reply_markup=keyboard
    )


# 🔥 ПРИЁМ ДАННЫХ ИЗ WEB APP (ЗАКАЗ)
@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def webapp_data(message: types.Message):
    # превращаем JSON-строку в словарь
    data = json.loads(message.web_app_data.data)

    order = data.get("order", {})
    total = data.get("total", 0)

    text = "✅ Заказ принят:\n\n"

    for item, qty in order.items():
        if qty > 0:
            text += f"• {item} × {qty}\n"

    text += f"\n💰 Сумма: {total} сум"

    await message.answer(text)


if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=lambda _: bot.delete_webhook(drop_pending_updates=True)
    )

