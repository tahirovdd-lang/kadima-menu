import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.filters.command import CommandObject

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN не найден. Добавь переменную окружения BOT_TOKEN на BotHost.")

ADMIN_ID = 6013591658
CHANNEL_ID = "@Kadimasignaturetaste"

# ✅ юзернейм бота без @
BOT_USERNAME = "kadima_cafe_bot"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


def kb_channel_to_bot() -> InlineKeyboardMarkup:
    # Ведём людей из канала в бота: /start menu
    url = f"https://t.me/{BOT_USERNAME}?start=menu"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍽 Открыть меню", url=url)]
    ])


def welcome_text() -> str:
    return (
        "✨ <b>Добро пожаловать в KADIMA Cafe!</b>\n\n"
        "🍽 Чтобы открыть меню, нажмите <b>синюю кнопку «Меню»</b> внизу чата.\n"
        "🛒 Там же можно оформить заказ.\n\n"
        "Если кнопка не видна — нажмите <b>/start</b> ещё раз."
    )


@dp.message(CommandStart())
async def start(message: types.Message, command: CommandObject):
    # args может быть "menu" (если пришли из канала), но текст можно оставить одинаковым
    await message.answer(welcome_text())


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

        # Авто-закреп (нужно право боту: "Закреплять сообщения")
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
        await message.answer(f"❌ Ошибка: <code>{e}</code>")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
