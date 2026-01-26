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
ADMIN_ID = 6013591658   # ← ТВОЙ TELEGRAM ID
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
        "👋 Добро пожаловать в <b>KADIMA Cafe</b>\nНажмите кнопку ниже, чтобы открыть меню:",
        reply_markup=kb
    )


# 🔥 ПРИЕМ ДАННЫХ ИЗ WEBAPP
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)

        order = data.get("order", {})
        total = data.get("total", 0)
        payment = data.get("payment", "не указано")
        order_type = data.get("type", "не указано")
        address = data.get("address", "—")
        phone = data.get("phone", "—")
        comment = data.get("comment", "—")

        # 🧾 Сообщение админу
        admin_text = "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n\n"

        for item, qty in order.items():
            if int(qty) > 0:
                admin_text += f"• {item} × {qty}\n"

        admin_text += (
            f"\n💰 <b>Сумма:</b> {total} сум"
            f"\n🚚 <b>Тип:</b> {order_type}"
            f"\n💳 <b>Оплата:</b> {payment}"
            f"\n📍 <b>Адрес:</b> {address}"
            f"\n📞 <b>Телефон:</b> {phone}"
            f"\n💬 <b>Комментарий:</b> {comment}"
        )

        # 📤 ОТПРАВКА АДМИНУ
        await bot.send_message(ADMIN_ID, admin_text)

        # 📩 ОТВЕТ КЛИЕНТУ
        await message.answer(
            "✅ <b>Ваш заказ принят!</b>\n"
            "Наш оператор свяжется с вами для подтверждения 📞"
        )

    except Exception as e:
        logging.error(e)
        await message.answer("❌ Ошибка обработки заказа")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
