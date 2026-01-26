import asyncio
import logging
import json
import os
import html

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6013591658
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"
CHANNEL_ID = "@Kadimasignaturetaste"

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN в BotHost.")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def esc(x) -> str:
    return html.escape(str(x)) if x is not None else "—"


def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🍽 Открыть меню / Menyuni ochish / Open menu",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
    )


START_TEXT_3LANG = (
    "👋 Добро пожаловать в <b>KADIMA Cafe</b>!\n"
    "Нажмите кнопку ниже, чтобы открыть меню.\n\n"
    "👋 <b>KADIMA Cafe</b> ga xush kelibsiz!\n"
    "Menyuni ochish uchun pastdagi tugmani bosing.\n\n"
    "👋 Welcome to <b>KADIMA Cafe</b>!\n"
    "Tap the button below to open the menu."
)

POST_TEXT_3LANG = (
    "🍽 <b>KADIMA Cafe</b>\n"
    "Нажмите кнопку ниже, чтобы открыть меню.\n\n"
    "🍽 <b>KADIMA Cafe</b>\n"
    "Menyuni ochish uchun pastdagi tugmani bosing.\n\n"
    "🍽 <b>KADIMA Cafe</b>\n"
    "Tap the button below to open the menu."
)


# ✅ Команда чтобы проверить реальный Telegram ID
@dp.message(Command("id"))
async def cmd_id(message: types.Message):
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n"
        f"chat_id: <code>{message.chat.id}</code>"
    )


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(START_TEXT_3LANG, reply_markup=menu_kb())


@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=POST_TEXT_3LANG,
            reply_markup=menu_kb()
        )
        await message.answer("✅ Пост с кнопкой меню отправлен в канал.")
    except Exception as e:
        logging.exception("CHANNEL POST ERROR")
        await message.answer(
            "❌ Не смог отправить в канал.\n"
            "Проверь:\n"
            "1) бот добавлен админом в канал\n"
            "2) есть право 'Публиковать сообщения'\n"
            "3) правильно указан CHANNEL_ID\n\n"
            f"Ошибка: <code>{esc(e)}</code>"
        )


# 🔥 ПРИЕМ ДАННЫХ ИЗ WEBAPP
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    # ✅ Быстрый ответ клиенту, чтобы видеть факт прихода данных
    try:
        await message.answer("✅ Данные заказа получены ботом. Обрабатываю…")
    except Exception:
        pass

    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {"_raw": raw}

    order = data.get("order") if isinstance(data, dict) else None
    if not isinstance(order, dict):
        order = {}

    total = str(data.get("total", "0")) if isinstance(data, dict) else "0"
    payment = str(data.get("payment", "не указано")) if isinstance(data, dict) else "не указано"
    order_type = str(data.get("type", "не указано")) if isinstance(data, dict) else "не указано"
    address = str(data.get("address", "—")) if isinstance(data, dict) else "—"
    phone = str(data.get("phone", "—")) if isinstance(data, dict) else "—"
    comment = str(data.get("comment", "—")) if isinstance(data, dict) else "—"

    tg = data.get("tg", {}) if isinstance(data, dict) else {}
    if not isinstance(tg, dict):
        tg = {}
    tg_id = tg.get("id", "")
    tg_username = tg.get("username", "")
    tg_first_name = tg.get("first_name", "")

    admin_text = "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n\n"

    if tg_id or tg_username or tg_first_name:
        admin_text += (
            f"👤 <b>Клиент:</b> {esc(tg_first_name)}\n"
            f"🆔 <b>ID:</b> {esc(tg_id)}\n"
            f"🔗 <b>Username:</b> @{esc(tg_username) if tg_username else '—'}\n\n"
        )

    if not order:
        admin_text += "⚠️ Корзина пустая\n"
    else:
        for item, qty in order.items():
            try:
                q = int(qty)
                if q > 0:
                    admin_text += f"• {esc(item)} × {q}\n"
            except Exception:
                if str(qty).strip():
                    admin_text += f"• {esc(item)} × {esc(qty)}\n"

    admin_text += (
        f"\n💰 <b>Сумма:</b> {esc(total)} сум"
        f"\n🚚 <b>Тип:</b> {esc(order_type)}"
        f"\n💳 <b>Оплата:</b> {esc(payment)}"
        f"\n📍 <b>Адрес:</b> {esc(address)}"
        f"\n📞 <b>Телефон:</b> {esc(phone)}"
        f"\n💬 <b>Комментарий:</b> {esc(comment)}"
    )

    try:
        await bot.send_message(ADMIN_ID, admin_text)
        await message.answer("✅ <b>Ваш заказ принят!</b>\nС вами скоро свяжется оператор 📞")
    except Exception as e:
        logging.exception("ADMIN SEND ERROR")
        await message.answer(
            "✅ <b>Ваш заказ принят!</b>\n"
            "⚠️ Но админу не удалось отправить уведомление.\n"
            f"Причина: <code>{esc(e)}</code>"
        )


# ✅ ДИАГНОСТИКА (НЕ ПЕРЕХВАТЫВАЕТ КОМАНДЫ)
@dp.message()
async def any_message_logger(message: types.Message):
    try:
        # команды не трогаем
        if message.text and message.text.startswith("/"):
            return
        logging.info(
            f"IN MSG: chat_id={message.chat.id} type={message.content_type} "
            f"from={message.from_user.id if message.from_user else None}"
        )
    except Exception:
        pass


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
