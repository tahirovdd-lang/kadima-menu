import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN на BotHost.")

# ✅ Админ (кто может вызывать /post_menu)
ADMIN_ID = 6013591658

# ✅ Канал
CHANNEL_ID = "@Kadimasignaturetaste"

# ✅ Бот (куда ведём людей из канала)
BOT_USERNAME = "kadima_cafe_bot"  # без @

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def channel_kb_to_bot() -> InlineKeyboardMarkup:
    # ВЕДЁМ В БОТА: /start menu
    url = f"https://t.me/{BOT_USERNAME}?start=menu"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🍽 Открыть меню", url=url)]]
    )


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот <b>KADIMA Cafe</b>.\n"
        "Из канала нажмите кнопку «Открыть меню», и я покажу вам приложение."
    )


@dp.message(Command("post_menu"))
async def post_menu(message: types.Message):
    """
    ВАРИАНТ №1:
    - бот публикует пост в канал
    - бот пытается ЗАКРЕПИТЬ пост (нужно право "Закреплять сообщения")
    """
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔️ Нет доступа.")

    text = (
        "🍽 <b>KADIMA Cafe</b>\n"
        "Нажмите кнопку ниже, чтобы открыть меню и оформить заказ:"
    )

    try:
        sent = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            reply_markup=channel_kb_to_bot()
        )

        # Пытаемся закрепить (если боту выдано право "Закреплять сообщения")
        pinned = False
        try:
            await bot.pin_chat_message(
                chat_id=CHANNEL_ID,
                message_id=sent.message_id,
                disable_notification=True
            )
            pinned = True
        except Exception:
            logging.exception("PIN ERROR")

        if pinned:
            await message.answer("✅ Пост отправлен в канал и закреплён.")
        else:
            await message.answer(
                "✅ Пост отправлен в канал.\n"
                "⚠️ Не удалось закрепить автоматически.\n"
                "Дай боту право «Закреплять сообщения» в канале или закрепи вручную."
            )

    except Exception as e:
        logging.exception("CHANNEL POST ERROR")
        await message.answer(
            "❌ Не смог отправить в канал.\n"
            "Проверь:\n"
            "1) бот админ канала\n"
            "2) есть право 'Публиковать сообщения'\n"
            "3) (для авто-закрепа) есть право 'Закреплять сообщения'\n"
            "4) CHANNEL_ID указан правильно\n\n"
            f"Ошибка: <code>{e}</code>"
        )


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
