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
    """Безопасно экранируем HTML, чтобы Telegram не ломал сообщение."""
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


@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    # 1) Парсим JSON безопасно
    data = {}
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {"_raw": raw}

    # 2) Вытаскиваем безопасно поля
    order = data.get("order") if isinstance(data, dict) else None
    if not isinstance(order, dict):
        order = {}

    total = data.get("total", "0") if isinstance(data, dict) else "0"
    payment = data.get("payment", "не указано") if isinstance(data, dict) else "не указано"
    order_type = data.get("type", "не указано") if isinstance(data, dict) else "не указано"
    address = data.get("address", "—") if isinstance(data, dict) else "—"
    phone = data.get("phone", "—") if isinstance(data, dict) else "—"
    comment = data.get("comment", "—") if isinstance(data, dict) else "—"

    # tg-данные клиента (приходят из WebApp, у тебя они отправляются)
    tg = data.get("tg", {}) if isinstance(data, dict) else {}
    if not isinstance(tg, dict):
        tg = {}
    tg_id = tg.get("id", "")
    tg_username = tg.get("username", "")
    tg_first_name = tg.get("first_name", "")

    # 3) Сообщение админу (ВАЖНО: всё экранируем)
    admin_text = "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n\n"

    # кто заказал
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

    if isinstance(data, dict) and "_raw" in data:
        admin_text += f"\n\n🧩 <b>RAW:</b>\n<code>{esc(data['_raw'])}</code>"

    # 4) Отправка админу (и покажем ошибку пользователю, если не отправилось)
    admin_sent = False
    admin_error = ""

    try:
        await bot.send_message(ADMIN_ID, admin_text)
        admin_sent = True
    except Exception as e:
        admin_error = str(e)
        logging.exception("ADMIN SEND ERROR")

    # 5) Ответ клиенту
    try:
        if admin_sent:
            await message.answer(
                "✅ <b>Ваш заказ принят!</b>\n"
                "С вами скоро свяжется оператор 📞"
            )
        else:
            await message.answer(
                "✅ <b>Ваш заказ принят!</b>\n"
                "⚠️ Но оператору не удалось отправить уведомление автоматически.\n"
                "Причина (для диагностики):\n"
                f"<code>{esc(admin_error) if admin_error else 'неизвестно'}</code>\n\n"
                "Проверь у админа:\n"
                "1) админ нажал /start у бота\n"
                "2) админ не блокировал бота\n"
                "3) в заказе/адресе нет спецсимволов, но мы уже экранируем — теперь должно работать"
            )
    except Exception:
        logging.exception("CLIENT ANSWER ERROR")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
