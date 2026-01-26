from aiogram import Bot, Dispatcher, executor, types
import logging
import json
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)


# ▶️ /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text="🍽 Открыть меню",
        web_app=types.WebAppInfo(url=WEBAPP_URL)
    ))

    await message.answer(
        "Добро пожаловать в <b>KADIMA Cafe</b> 👋\nНажмите кнопку ниже, чтобы открыть меню:",
        reply_markup=kb
    )


# 🔥 ПРИЁМ ДАННЫХ ИЗ WEB APP
@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA)
async def webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        order = data.get("order", {})
        total = data.get("total", 0)

        text = "✅ <b>Заказ принят:</b>\n\n"

        for item, qty in order.items():
            if qty > 0:
                text += f"• {item} × {qty}\n"

        text += f"\n💰 <b>Сумма:</b> {total} сум"

        await message.answer(text)

    except Exception as e:
        await message.answer("Ошибка обработки заказа ❌")
        logging.error(e)


# 🚨 КЛЮЧЕВОЕ — УДАЛЯЕМ WEBHOOK ПЕРЕД ЗАПУСКОМ
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)
    print("Webhook удалён. Бот работает через polling.")


if __name__ == "__main__":
    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )


