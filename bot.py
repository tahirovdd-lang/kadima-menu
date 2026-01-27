import asyncio
import logging
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import CommandObject
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN.")

BOT_USERNAME = os.getenv("BOT_USERNAME")  # например: KadimaSignatureBot (без @)
if not BOT_USERNAME:
    raise RuntimeError("❌ BOT_USERNAME не найден. Добавь переменную окружения BOT_USERNAME (без @).")

ADMIN_ID = 6013591658
CHANNEL_ID = "@Kadimasignaturetaste"

WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def kb_webapp_reply() -> ReplyKeyboardMarkup:
    # кнопка в личке — лучший вариант для гарантированного web_app_data
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )


def kb_channel_deeplink() -> InlineKeyboardMarkup:
    # ✅ Кнопка для канала: открывает бота и WebApp через startapp (это критично)
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
async def start(message: types.Message, command: CommandObject):
    # startapp=menu тоже попадает сюда как args
    args = (command.args or "").strip().lower()

    # Всегда показываем кнопку WebApp в личке
    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())

    # Если пришли из канала через startapp=menu — можно дополнительно подсказать
    if "menu" in args:
        await message.answer("✅ Меню откроется по кнопке ниже. После оформления заказа он придёт сюда.")


@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    text = (
        "🍽 <b>KADIMA Cafe</b>\n"
        "Нажмите кнопку ниже, чтобы открыть меню:"
    )

    try:
        sent = await bot.send_message(CHANNEL_ID, text, reply_markup=kb_channel_deeplink())
        # закреп — по желанию, но бот должен быть админом канала с правом закрепа
        try:
            await bot.pin_chat_message(CHANNEL_ID, sent.message_id, disable_notification=True)
            await message.answer("✅ Пост отправлен в канал и закреплён.")
        except Exception:
            await message.answer(
                "✅ Пост отправлен в канал.\n"
                "⚠️ Не удалось закрепить автоматически — дай боту право «Закреплять сообщения» или закрепи вручную."
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


@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    # Если эта строка НЕ появляется у клиента — значит web_app_data не приходит
    await message.answer("✅ <b>Получил заказ из меню.</b>\nОбрабатываю…")

    try:
        data = json.loads(raw) if raw else {}
        if not isinstance(data, dict):
            data = {"_raw": raw}
    except Exception:
        data = {"_raw": raw}

    order = data.get("order", {})
    if not isinstance(order, dict):
        order = {}

    total_num = int(data.get("total_num", 0) or 0)
    total_str = str(data.get("total", "") or fmt_sum(total_num))

    payment = str(data.get("payment", "—"))
    order_type = str(data.get("type", "—"))
    address = str(data.get("address", "—"))
    phone = str(data.get("phone", "—"))
    comment = str(data.get("comment", "—"))

    order_id = str(data.get("order_id", "—"))
    created_at = str(data.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    pay_label = {"cash": "💵 Наличные", "click": "💳 CLICK"}.get(payment, payment)
    type_label = {"delivery": "🚚 Доставка", "pickup": "🏃 Самовывоз"}.get(order_type, order_type)

    admin_text = (
        "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n"
        f"🆔 <b>{order_id}</b>\n"
        f"🕒 {created_at}\n\n"
    )

    if not order:
        admin_text += "⚠️ Корзина пустая (order пустой)\n"
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
        f"\n💰 <b>Сумма:</b> {total_str} сум"
        f"\n🚚 <b>Тип:</b> {type_label}"
        f"\n💳 <b>Оплата:</b> {pay_label}"
        f"\n📍 <b>Адрес:</b> {address}"
        f"\n📞 <b>Телефон:</b> {phone}"
        f"\n💬 <b>Комментарий:</b> {comment}"
        f"\n\n👤 <b>Клиент:</b> {message.from_user.full_name} (id: <code>{message.from_user.id}</code>)"
    )

    # Отправляем админу
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        logging.info("ORDER SENT TO ADMIN")
    except Exception as e:
        logging.exception("ADMIN SEND ERROR")
        await message.answer(
            "⚠️ Я получил заказ, но не смог отправить админу.\n"
            "Проверь, что админ запускал бота (/start) и бот не заблокирован.\n"
            f"Ошибка: <code>{e}</code>"
        )
        return

    # Финальный ответ клиенту
    await message.answer(
        "✅ <b>Ваш заказ принят!</b>\n"
        f"Номер: <b>{order_id}</b>\n"
        f"Сумма: <b>{total_str}</b> сум\n\n"
        "С вами скоро свяжется оператор 📞"
    )


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
