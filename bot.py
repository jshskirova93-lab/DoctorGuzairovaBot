import os

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    try:
        from config import TOKEN
    except (ImportError, ValueError):
        TOKEN = None

if not TOKEN:
    raise RuntimeError(
        "Токен Telegram-бота не найден. "
        "Добавьте переменную окружения BOT_TOKEN."
    )