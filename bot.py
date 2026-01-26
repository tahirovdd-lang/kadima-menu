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
ADMIN_ID = 6013591658
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# ▶️ СТАРТ
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
        "👋 Добро пожаловать в <b>KADIMA Cafe</b>\n"
        "Нажмите кнопку ниже, чтобы открыть меню:",
        reply_markup=kb
    )


# 🔥 ПРИЕМ ДАННЫХ ИЗ WEBAPP
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    try:
        raw = message.web_app_data.data
        logging.info(f"WEBAPP DATA RAW: {raw}")

        data = json.loads(raw)

        order = data.get("order") or {}
        total = str(data.get("total") or "0")
        payment = str(data.get("payment") or "не указано")
        order_type = str(data.get("type") or "не указано")
        address = str(data.get("address") or "—")
        phone = str(data.get("phone") or "—")
        comment = str(data.get("comment") or "—")

        # 🧾 СООБЩЕНИЕ АДМИНУ
        admin_text = "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n\n"

        if not order:
            admin_text += "⚠️ Корзина пустая\n"
        else:
            for item, qty in order.items():
                try:
                    if int(qty) > 0:
                        admin_text += f"• {item} × {qty}\n"
                except:
                    pass

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
            "С вами скоро свяжется оператор 📞"
        )

        logging.info("ORDER SENT TO ADMIN SUCCESSFULLY")

    except Exception as e:
        logging.exception("ORDER PROCESSING ERROR")
        await message.answer("❌ Ошибка обработки заказа")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
