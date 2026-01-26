import asyncio
import logging
import json
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()


# ▶️ /start
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🍽 Открыть меню",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
    )

    await message.answer(
        "Добро пожаловать в <b>KADIMA Cafe</b> 👋\nНажмите кнопку ниже, чтобы открыть меню:",
        reply_markup=kb
    )


# 🔥 ПРИЁМ ДАННЫХ ИЗ WEB APP
@dp.message(lambda message: message.web_app_data is not None)
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


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())




