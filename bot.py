import asyncio
import logging
import json
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 👉 ВСТАВЬ СЮДА СВОЙ TELEGRAM ID
ADMIN_ID = 6013591658

WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# ▶️ КНОПКА ОТКРЫТЬ МЕНЮ
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


# 🔥 ПОЛУЧЕНИЕ ЗАКАЗА ИЗ WEB APP
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)

        order = data.get("order", {})
        total = data.get("total", 0)
        phone = data.get("phone", "не указан")
        address = data.get("address", "самовывоз")
        comment = data.get("comment", "нет")
        payment = data.get("payment", "cash")
        order_type = data.get("type", "delivery")

        admin_text = "🆕 <b>НОВЫЙ ЗАКАЗ</b>\n\n"

        for item, qty in order.items():
            admin_text += f"• {item} × {qty}\n"

        admin_text += (
            f"\n💰 Сумма: <b>{total} сум</b>\n"
            f"📞 Телефон: {phone}\n"
            f"📍 Адрес: {address}\n"
            f"💬 Комментарий: {comment}\n"
            f"💳 Оплата: {payment}\n"
            f"🚚 Тип: {order_type}"
        )

        # ✅ АДМИНУ
        await bot.send_message(ADMIN_ID, admin_text)

        # ✅ КЛИЕНТУ
        await message.answer(
            "✅ Ваш заказ принят!\nСкоро с вами свяжется оператор 📞"
        )

    except Exception as e:
        logging.error(e)
        await message.answer("Ошибка обработки заказа ❌")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
