import asyncio
import logging
import json
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN на BotHost.")

ADMIN_ID = 6013591658
CHANNEL_ID = "@Kadimasignaturetaste"
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# --- Кнопка WebApp (только для лички/группы, НЕ для канала)
def kb_webapp() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )


# --- Кнопка для канала (только URL, иначе BUTTON_TYPE_INVALID)
def kb_channel_url() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Открыть меню", url=WEBAPP_URL)]
        ]
    )


# /start в личке
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в <b>KADIMA Cafe</b>\n"
        "Нажмите кнопку ниже, чтобы открыть меню:",
        reply_markup=kb_webapp()
    )


# Команда для админа — публикуем пост в канал
@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text="🍽 <b>KADIMA Cafe</b>\nНажмите кнопку ниже, чтобы открыть меню:",
            reply_markup=kb_channel_url()  # ВАЖНО: только url=
        )
        await message.answer("✅ Пост с кнопкой отправлен в канал.")
    except Exception as e:
        logging.exception("CHANNEL POST ERROR")
        await message.answer(
            "❌ Не смог отправить в канал.\n"
            "Проверь:\n"
            "1) бот админ канала\n"
            "2) есть право 'Публиковать сообщения'\n"
            "3) CHANNEL_ID указан правильно\n\n"
            f"Ошибка: <code>{e}</code>"
        )


# Приём данных из WebApp
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    # Безопасный парс JSON
    try:
        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            data = {"_raw": raw}
    except Exception:
        data = {"_raw": raw}

    order = data.get("order", {})
    if not isinstance(order, dict):
        order = {}

    total = str(data.get("total", "0"))
    payment = str(data.get("payment", "не указано"))
    order_type = str(data.get("type", "не указано"))
    address = str(data.get("address", "—"))
    phone = str(data.get("phone", "—"))
    comment = str(data.get("comment", "—"))

    admin_text = "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n\n"

    if not order:
        admin_text += "⚠️ Корзина пустая\n"
    else:
        for item, qty in order.items():
            try:
                q = int(qty)
                if q > 0:
                    admin_text += f"• {item} × {q}\n"
            except Exception:
                if str(qty).strip():
                    admin_text += f"• {item} × {qty}\n"

    admin_text += (
        f"\n💰 <b>Сумма:</b> {total} сум"
        f"\n🚚 <b>Тип:</b> {order_type}"
        f"\n💳 <b>Оплата:</b> {payment}"
        f"\n📍 <b>Адрес:</b> {address}"
        f"\n📞 <b>Телефон:</b> {phone}"
        f"\n💬 <b>Комментарий:</b> {comment}"
    )

    # Если пришёл сырой текст (не JSON) — добавим для диагностики
    if "_raw" in data:
        admin_text += f"\n\n🧩 <b>RAW:</b>\n<code>{data['_raw']}</code>"

    # Отправка админу (админ должен был нажать /start у бота хотя бы 1 раз)
    admin_sent = False
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        admin_sent = True
    except Exception:
        logging.exception("ADMIN SEND ERROR")

    # Ответ клиенту
    try:
        if admin_sent:
            await message.answer("✅ <b>Ваш заказ принят!</b>\nС вами скоро свяжется оператор 📞")
        else:
            await message.answer(
                "✅ <b>Ваш заказ принят!</b>\n"
                "⚠️ Но оператору не удалось получить уведомление автоматически.\n"
                "Пожалуйста, позвоните в кафе."
            )
    except Exception:
        logging.exception("CLIENT ANSWER ERROR")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
