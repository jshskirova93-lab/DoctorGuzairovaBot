import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not TOKEN:
    raise ValueError("Переменная BOT_TOKEN не задана")

if not ADMIN_CHAT_ID:
    raise ValueError("Переменная ADMIN_CHAT_ID не задана")

ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)