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
ADMIN_ID = 8145095421
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
        "Choose your favorite dishes and place an order — ju
