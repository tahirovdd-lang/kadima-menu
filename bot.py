import asyncio
import logging
import json
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import CommandObject

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN на BotHost.")

ADMIN_ID = 6013591658
CHANNEL_ID = "@Kadimasignaturetaste"
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

# ✅ ТВОЙ БОТ (без @)
BOT_USERNAME = "kadima_cafe_bot"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# --- Кнопка WebApp (только для лички/группы, НЕ для канала)
def kb_webapp() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )


# --- Кнопка для канала: ведёт в бота (/start menu), а уже в боте открывают WebApp
def kb_channel_to_bot() -> InlineKeyboardMarkup:
    url = f"https://t.me/{BOT_USERNAME}?start=menu"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Открыть меню", url=url)]
        ]
    )


# /start в личке (и обработка payload: /start menu)
@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    # command.args будет "menu", если человек пришёл из канала по ссылке start=menu
    args = (command.args or "").strip().lower()

    if args == "menu":
        await message.answer(
            "🍽 <b>KADIMA Cafe</b>\n"
            "Откройте меню кнопкой ниже:",
            reply_markup=kb_webapp()
        )
        return

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
            reply_markup=kb_channel_to_bot()
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

    order = data.get("order", {}) if isinstance(data, dict) else {}
    if not isinstance(order, dict):
        order = {}

    total = str(data.get("total", "0")) if isinstance(data, dict) else "0"
    payment = str(data.get("payment", "не указано")) if isinstance(data, dict) else "не указано"
    order_type = str(data.get("type", "не указано")) if isinstance(data, dict) else "не указано"
    address = str(data.get("address", "—")) if isinstance(data, dict) else "—"
    phone = str(data.get("phone", "—")) if isinstance(data, dict) else "—"
    comment = str(data.get("comment", "—")) if isinstance(data, dict) else "—"

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
    if isinstance(data, dict) and "_raw" in data:
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
