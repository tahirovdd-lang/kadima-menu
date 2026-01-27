import asyncio
import logging
import json
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN на BotHost.")

ADMIN_ID = 6013591658
CHANNEL_ID = "@Kadimasignaturetaste"
BOT_USERNAME = "kadima_cafe_bot"  # без @

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def kb_channel_to_bot() -> InlineKeyboardMarkup:
    # ведём в бота: /start menu
    url = f"https://t.me/{BOT_USERNAME}?start=menu"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Открыть меню", url=url)]
    ])


def welcome_text(from_channel: bool) -> str:
    if from_channel:
        return (
            "✨ <b>KADIMA Cafe</b>\n\n"
            "Чтобы открыть меню, нажмите <b>синюю кнопку «Меню»</b> внизу чата.\n"
            "После оформления заказа вы получите подтверждение здесь ✅"
        )
    return (
        "✨ <b>Добро пожаловать в KADIMA Cafe!</b>\n\n"
        "🍽 Нажмите <b>синюю кнопку «Меню»</b> внизу чата, чтобы открыть меню.\n"
        "✅ После заказа мы пришлём подтверждение сюда."
    )


@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    args = (command.args or "").strip().lower()
    await message.answer(welcome_text(from_channel=(args == "menu")))


@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    text = (
        "🍽 <b>KADIMA Cafe</b>\n"
        "Нажмите кнопку ниже, чтобы перейти в бота и открыть меню:"
    )

    try:
        sent = await bot.send_message(CHANNEL_ID, text, reply_markup=kb_channel_to_bot())

        # попытка закрепа (нужно право боту: Закреплять сообщения)
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
    """
    Диагностика: может ли бот писать админу.
    """
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    try:
        await bot.send_message(ADMIN_ID, "✅ Тест: бот может отправлять сообщения админу.")
        await message.answer("✅ Проверка пройдена: админу отправлено сообщение.")
    except Exception as e:
        logging.exception("PING ADMIN ERROR")
        await message.answer(
            "❌ Бот НЕ может написать админу.\n"
            "Причины:\n"
            "1) админ не нажал /start у бота\n"
            "2) админ заблокировал бота\n\n"
            f"Ошибка: <code>{e}</code>"
        )


@dp.message(Command("debug_webapp"))
async def debug_webapp(message: types.Message):
    await message.answer(
        "🧩 <b>Проверка WebApp</b>\n\n"
        "Чтобы бот получил заказ, WebApp должен вызвать:\n"
        "<code>Telegram.WebApp.sendData(JSON.stringify({...}))</code>\n\n"
        "Если после оформления заказа бот НЕ отвечает — значит sendData не вызывается "
        "или отправляется не JSON."
    )


# ✅ Приём данных из WebApp
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    # 1) парсим данные максимально безопасно
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

    # 2) собираем текст админу
    admin_text = "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n\n"

    if not order:
        admin_text += "⚠️ Корзина пустая или не пришла (order пуст)\n"
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
        f"\n\n👤 <b>Клиент:</b> {message.from_user.full_name} (id: <code>{message.from_user.id}</code>)"
    )

    if "_raw" in data:
        admin_text += f"\n\n🧩 <b>RAW:</b>\n<code>{data['_raw']}</code>"

    # 3) сначала ответ клиенту (чтобы он точно видел подтверждение)
    try:
        await message.answer("✅ <b>Ваш заказ принят!</b>\nС вами скоро свяжется оператор 📞")
    except Exception:
        logging.exception("CLIENT ANSWER ERROR")

    # 4) отправляем админу
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        logging.info("ORDER SENT TO ADMIN")
    except Exception as e:
        logging.exception("ADMIN SEND ERROR")
        # если админу не отправилось — скажем клиенту, что оператор может не увидеть
        try:
            await message.answer(
                "⚠️ Не удалось автоматически отправить заказ оператору.\n"
                "Пожалуйста, позвоните в кафе или напишите нам."
            )
        except Exception:
            pass


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
