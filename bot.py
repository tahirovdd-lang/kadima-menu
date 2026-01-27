import asyncio
import logging
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN.")

BOT_USERNAME = "kadima_cafe_bot"  # без @

ADMIN_ID = 6013591658
CHANNEL_ID = "@Kadimasignaturetaste"
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def kb_webapp_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )


def kb_channel_deeplink() -> InlineKeyboardMarkup:
    deeplink = f"https://t.me/{BOT_USERNAME}?startapp=menu"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Открыть меню", url=deeplink)]
    ])


def welcome_text() -> str:
    return (
        "✨ <b>KADIMA Cafe</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть меню.\n"
        "✅ После заказа мы пришлём подтверждение сюда."
    )


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())


@dp.message(Command("startapp"))
async def startapp(message: types.Message):
    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())


@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    text = "🍽 <b>KADIMA Cafe</b>\nНажмите кнопку ниже, чтобы открыть меню:"
    try:
        sent = await bot.send_message(CHANNEL_ID, text, reply_markup=kb_channel_deeplink())
        try:
            await bot.pin_chat_message(CHANNEL_ID, sent.message_id, disable_notification=True)
            await message.answer("✅ Пост отправлен в канал и закреплён.")
        except Exception:
            await message.answer(
                "✅ Пост отправлен в канал.\n"
                "⚠️ Не удалось закрепить — дай боту право «Закреплять сообщения» или закрепи вручную."
            )
    except Exception as e:
        logging.exception("CHANNEL POST ERROR")
        await message.answer(f"❌ Ошибка отправки в канал: <code>{e}</code>")


@dp.message(Command("ping_admin"))
async def ping_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")
    try:
        await bot.send_message(ADMIN_ID, "✅ Тест: бот может отправлять сообщения админу.")
        await message.answer("✅ Проверка пройдена: админу отправлено сообщение.")
    except Exception as e:
        logging.exception("PING ADMIN ERROR")
        await message.answer(f"❌ Не смог написать админу. Ошибка: <code>{e}</code>")


def fmt_sum(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        n = 0
    return f"{n:,}".replace(",", " ")


def tg_label(u: types.User) -> str:
    # Ник под телефоном (если нет ника — имя)
    if u.username:
        return f"@{u.username}"
    return u.full_name


def clean_str(v) -> str:
    s = "" if v is None else str(v)
    s = s.strip()
    return s


@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    # Клиенту (служебное короткое подтверждение обработки)
    await message.answer("✅ <b>Получил заказ.</b> Обрабатываю…")

    # Парсим JSON
    try:
        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            data = {"_raw": raw}
    except Exception:
        data = {"_raw": raw}

    order = data.get("order", {})
    if not isinstance(order, dict):
        order = {}

    # Итоги
    total_num = int(data.get("total_num", 0) or 0)
    total_str = clean_str(data.get("total")) or fmt_sum(total_num)

    payment = clean_str(data.get("payment")) or "—"
    order_type = clean_str(data.get("type")) or "—"
    address = clean_str(data.get("address")) or "—"
    phone = clean_str(data.get("phone")) or "—"
    comment = clean_str(data.get("comment"))

    order_id = clean_str(data.get("order_id")) or "—"
    created_at = clean_str(data.get("created_at")) or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pay_label = {"cash": "💵 Наличные", "click": "💳 Безнал (CLICK)"} .get(payment, payment)
    type_label = {"delivery": "🚚 Доставка", "pickup": "🏃 Самовывоз"} .get(order_type, order_type)

    # Список позиций
    lines = []
    for item, qty in order.items():
        try:
            q = int(qty)
        except Exception:
            q = qty
        if isinstance(q, int) and q <= 0:
            continue
        lines.append(f"• {item} × {q}")

    if not lines:
        lines = ["⚠️ Корзина пустая"]

    # ✅ Сообщение админу: ник под телефоном, без отдельной строки "Клиент:"
    admin_text = (
        "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n"
        f"🆔 <b>{order_id}</b>\n"
        f"🕒 {created_at}\n\n"
        + "\n".join(lines) +
        f"\n\n💰 <b>Сумма:</b> {total_str} сум"
        f"\n🚚 <b>Тип:</b> {type_label}"
        f"\n💳 <b>Оплата:</b> {pay_label}"
        f"\n📍 <b>Адрес:</b> {address}"
        f"\n📞 <b>Телефон:</b> {phone}"
        f"\n👤 <b>Telegram:</b> {tg_label(message.from_user)}"
    )

    if comment:
        admin_text += f"\n💬 <b>Комментарий:</b> {comment}"

    # Отправляем админу
    try:
        await bot.send_message(ADMIN_ID, admin_text)
    except Exception as e:
        logging.exception("ADMIN SEND ERROR")
        return await message.answer(
            "⚠️ Заказ получил, но админу отправить не смог.\n"
            "Проверь: админ сделал /start боту и не блокировал.\n"
            f"Ошибка: <code>{e}</code>"
        )

    # ✅ Сообщение клиенту: его заказ + адрес/коммент/оплата + спасибо
    client_text = (
        "✅ <b>Ваш заказ принят!</b>\n"
        "🙏 Спасибо за заказ!\n\n"
        f"🆔 <b>{order_id}</b>\n\n"
        "<b>Состав заказа:</b>\n"
        + "\n".join(lines) +
        f"\n\n💰 <b>Сумма:</b> {total_str} сум"
        f"\n🚚 <b>Тип:</b> {type_label}"
        f"\n💳 <b>Оплата:</b> {pay_label}"
        f"\n📍 <b>Адрес:</b> {address}"
        f"\n📞 <b>Телефон:</b> {phone}"
    )
    if comment:
        client_text += f"\n💬 <b>Комментарий:</b> {comment}"

    await message.answer(client_text)


@dp.message()
async def fallback(message: types.Message):
    await message.answer("🤖 Я на связи. Нажми /start")


async def main():
    # Важно: если был webhook — polling не получит апдейты
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
