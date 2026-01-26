import asyncio
import logging
import json
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ твой админ (чтобы получать заказы и иметь доступ к команде /post_menu)
ADMIN_ID = 6013591658

# ✅ твой WebApp
WEBAPP_URL = "https://tahirovdd-lang.github.io/kadima-menu/"

# ✅ твой канал
CHANNEL_ID = "@Kadimasignaturetaste"

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN в BotHost.")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )


# ▶️ СТАРТ (в личке/группе)
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в <b>KADIMA Cafe</b>\n"
        "Нажмите кнопку ниже, чтобы открыть меню:",
        reply_markup=menu_kb()
    )


# 📢 Публикация поста в канал с кнопкой меню
# Запускать в личке с ботом: /post_menu  (только админ)
@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text="🍽 <b>KADIMA Cafe</b>\nНажмите кнопку ниже, чтобы открыть меню:",
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
            f"Ошибка: <code>{e}</code>"
        )


# 🔥 ПРИЕМ ДАННЫХ ИЗ WEBAPP
@dp.message(F.web_app_data)
async def webapp_data(message: types.Message):
    raw = message.web_app_data.data
    logging.info(f"WEBAPP DATA RAW: {raw}")

    # 1) Пытаемся распарсить JSON, но не падаем если формат неожиданный
    data = None
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {"_raw": raw}

    # 2) Вытаскиваем поля максимально безопасно
    order = data.get("order") if isinstance(data, dict) else None
    if not isinstance(order, dict):
        order = {}

    total = str(data.get("total", "0")) if isinstance(data, dict) else "0"
    payment = str(data.get("payment", "не указано")) if isinstance(data, dict) else "не указано"
    order_type = str(data.get("type", "не указано")) if isinstance(data, dict) else "не указано"
    address = str(data.get("address", "—")) if isinstance(data, dict) else "—"
    phone = str(data.get("phone", "—")) if isinstance(data, dict) else "—"
    comment = str(data.get("comment", "—")) if isinstance(data, dict) else "—"

    # 3) Формируем сообщение админу
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
                # если qty не число — всё равно покажем
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

    # Если пришёл не-JSON, приложим сырой текст (чтобы понять, что реально отправляет WebApp)
    if isinstance(data, dict) and "_raw" in data:
        admin_text += f"\n\n🧩 <b>RAW:</b>\n<code>{data['_raw']}</code>"

    # 4) Отправка админу + ответ клиенту
    # ВАЖНО: админу придёт только если админ нажал /start у бота хотя бы 1 раз.
    admin_sent = False
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        admin_sent = True
    except Exception as e:
        logging.exception("ADMIN SEND ERROR")

    try:
        if admin_sent:
            await message.answer("✅ <b>Ваш заказ принят!</b>\nС вами скоро свяжется оператор 📞")
        else:
            await message.answer(
                "✅ <b>Ваш заказ принят!</b>\n"
                "⚠️ Но оператору не удалось отправить уведомление автоматически.\n"
                "Пожалуйста, позвоните в кафе или напишите в чат."
            )
    except Exception:
        logging.exception("CLIENT ANSWER ERROR")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
