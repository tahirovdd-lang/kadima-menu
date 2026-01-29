import asyncio
import logging
import json
import os
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    InlineKeyboardMarkup, InlineKeyboardButton
)

logging.basicConfig(level=logging.INFO)

# ====== НАСТРОЙКИ ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN.")

BOT_USERNAME = "kadima_cafe_bot"  # без @
ADMIN_ID = 8145095421             # ✅ ОБНОВЛЁННЫЙ ADMIN ID
CHANNEL_ID = "@Kadimasignaturetaste"

# ⚠️ ВАЖНО: версия, чтобы Telegram не кешировал старый сайт
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/?v=3"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# ====== АНТИ-ДУБЛЬ START ======
_last_start: dict[int, float] = {}

def allow_start(user_id: int, ttl: float = 2.0) -> bool:
    now = time.time()
    prev = _last_start.get(user_id, 0.0)
    if now - prev < ttl:
        return False
    _last_start[user_id] = now
    return True


# ====== КНОПКИ ======
BTN_OPEN_MULTI = "Ochish • Открыть • Open"

def kb_webapp_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_OPEN_MULTI, web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )

def kb_channel_deeplink() -> InlineKeyboardMarkup:
    deeplink = f"https://t.me/{BOT_USERNAME}?startapp=menu"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=BTN_OPEN_MULTI, url=deeplink)]]
    )


# ====== ТЕКСТ ======
def welcome_text() -> str:
    return (
        "🇷🇺 Добро пожаловать в <b>KADIMA</b>! 👋 "
        "Выберите любимые блюда и оформите заказ — просто нажмите «Открыть» ниже.\n\n"
        "🇺🇿 <b>KADIMA</b> ga xush kelibsiz! 👋 "
        "Sevimli taomlaringizni tanlang va buyurtma bering — buning uchun pastdagi «Ochish» tugmasini bosing.\n\n"
        "🇬🇧 Welcome to <b>KADIMA</b>! 👋 "
        "Choose your favorite dishes and place an order — just tap “Open” below."
    )


# ====== /start ======
@dp.message(CommandStart())
async def start(message: types.Message):
    if not allow_start(message.from_user.id):
        return
    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())

@dp.message(Command("startapp"))
async def startapp(message: types.Message):
    if not allow_start(message.from_user.id):
        return
    await message.answer(welcome_text(), reply_markup=kb_webapp_reply())


# ====== ПОСТ В КАНАЛ ======
@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    text = (
        "🇷🇺 <b>KADIMA</b>\nНажмите кнопку ниже, чтобы открыть меню.\n\n"
        "🇺🇿 <b>KADIMA</b>\nPastdagi tugma orqali menyuni oching.\n\n"
        "🇬🇧 <b>KADIMA</b>\nTap the button below to open the menu."
    )

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


# ====== ВСПОМОГАТЕЛЬНЫЕ ======
def fmt_sum(n: int) -> str:
    try:
        n = int(n)
    except Exception:
        n = 0
    return f"{n:,}".replace(",", " ")

def tg_label(u: types.User) -> str:
    return f"@{u.username}" if u.username else u.full_name

def clean_str(v) -> str:
    return ("" if v is None else str(v)).strip()


# ====== ЗАКАЗ ИЗ WEBAPP ======
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    await message.answer("✅ <b>Получил заказ.</b> Обрабатываю…")

    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}

    order = data.get("order", {})
    total_num = int(data.get("total_num", 0) or 0)
    total_str = clean_str(data.get("total")) or fmt_sum(total_num)

    payment = clean_str(data.get("payment")) or "—"
    order_type = clean_str(data.get("type")) or "—"
    address = clean_str(data.get("address")) or "—"
    phone = clean_str(data.get("phone")) or "—"
    comment = clean_str(data.get("comment"))
    order_id = clean_str(data.get("order_id")) or "—"

    pay_label = {"cash": "💵 Наличные", "click": "💳 Безнал (CLICK)"}.get(payment, payment)
    type_label = {"delivery": "🚚 Доставка", "pickup": "🏃 Самовывоз"}.get(order_type, order_type)

    lines = [f"• {item} × {qty}" for item, qty in order.items() if int(qty) > 0] or ["⚠️ Корзина пустая"]

    admin_text = (
        "🚨 <b>НОВЫЙ ЗАКАЗ KADIMA</b>\n"
        f"🆔 <b>{order_id}</b>\n\n"
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

    await bot.send_message(ADMIN_ID, admin_text)

    await message.answer(
        "✅ <b>Ваш заказ принят!</b>\n"
        "🙏 Спасибо за заказ!\n\n"
        f"🆔 <b>{order_id}</b>\n\n"
        + "\n".join(lines) +
        f"\n\n💰 <b>Сумма:</b> {total_str} сум"
    )


# ====== ЗАПУСК ======
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
