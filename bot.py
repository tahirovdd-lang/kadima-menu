import asyncio
import logging
import json
import os

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

ADMIN_ID = 6013591658
CHANNEL_ID = "@Kadimasignaturetaste"

# ✅ твой WebApp URL
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"


bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def kb_webapp_reply() -> ReplyKeyboardMarkup:
    # ✅ синяя кнопка внизу чата (именно она нужна для web_app_data)
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True
    )


def kb_webapp_inline() -> InlineKeyboardMarkup:
    # ✅ кнопка внутри сообщения (подходит для канала)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])


def welcome_text(from_channel: bool) -> str:
    if from_channel:
        return (
            "✨ <b>KADIMA Cafe</b>\n\n"
            "Нажмите кнопку ниже, чтобы открыть меню.\n"
            "После оформления заказа вы получите подтверждение здесь ✅"
        )
    return (
        "✨ <b>Добро пожаловать в KADIMA Cafe!</b>\n\n"
        "Нажмите кнопку ниже, чтобы открыть меню.\n"
        "✅ После заказа мы пришлём подтверждение сюда."
    )


@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    args = (command.args or "").strip().lower()
    await message.answer(
        welcome_text(from_channel=(args == "menu")),
        reply_markup=kb_webapp_reply()
    )


@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    text = (
        "🍽 <b>KADIMA Cafe</b>\n"
        "Нажмите кнопку ниже, чтобы открыть меню:"
    )

    try:
        sent = await bot.send_message(CHANNEL_ID, text, reply_markup=kb_webapp_inline())
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

    # ✅ Если это сообщение не появляется у клиента — значит web_app_data не приходит вообще
    await message.answer("✅ <b>Получил заказ из меню.</b>\nОбрабатываю…")

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

    total_num = int(data.get("total_num", 0) or 0)
    total_str = str(data.get("total", "") or fmt_sum(total_num))

    payment = str(data.get("payment", "—"))
    order_type = str(data.get("type", "—"))
    address = str(data.get("address", "—"))
    phone = str(data.get("phone", "—"))
    comment = str(data.get("comment", "—"))

    order_id = str(data.get("order_id", "—"))
    created_at = str(data.get("created_at", "—"))

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
        await message.answer(f"⚠️ Не смог отправить админу: <code>{e}</code>")
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
