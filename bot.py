import os
import re
import secrets
import smtplib
import ssl
import time
from collections import defaultdict, deque
from email.message import EmailMessage

from aiohttp import web
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

from keyboards import main_keyboard
from handlers import (
    ADMIN_CHAT_ID,
    menu,
    start_questionnaire,
    receive_name,
    receive_age,
    receive_height,
    receive_weight,
    receive_phone,
    receive_preferred_time,
    receive_complaints,
    confirm_application,
    cancel_questionnaire,
    start_admin_reply,
    send_admin_reply,
    start_patient_reply,
    send_patient_reply,
    cancel_message_reply,
    NAME,
    AGE,
    HEIGHT,
    WEIGHT,
    PHONE,
    PREFERRED_TIME,
    COMPLAINTS,
    CONFIRM_APPLICATION,
    ADMIN_REPLY,
    PATIENT_REPLY,
)


DEFAULT_ALLOWED_ORIGINS = {
    "https://doctorgulnaz.ru",
    "https://www.doctorgulnaz.ru",
}
RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 10 * 60
request_history: dict[str, deque[float]] = defaultdict(deque)


def allowed_origins() -> set[str]:
    """Домены, которым разрешено отправлять заявки."""

    configured = os.getenv("ALLOWED_ORIGINS", "")
    if not configured.strip():
        return DEFAULT_ALLOWED_ORIGINS

    return {
        origin.strip().rstrip("/")
        for origin in configured.split(",")
        if origin.strip()
    }


def cors_headers(origin: str) -> dict[str, str]:
    """CORS-заголовки только для официального сайта."""

    if origin.rstrip("/") not in allowed_origins():
        return {}

    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


def client_ip(request: web.Request) -> str:
    """IP посетителя с учётом прокси Railway."""

    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.remote or "unknown"


def rate_limit_exceeded(ip_address: str) -> bool:
    """Не более пяти заявок с одного IP за десять минут."""

    now = time.monotonic()
    history = request_history[ip_address]

    while history and now - history[0] > RATE_LIMIT_WINDOW_SECONDS:
        history.popleft()

    if len(history) >= RATE_LIMIT_REQUESTS:
        return True

    history.append(now)
    return False


def clean_text(value, max_length: int) -> str:
    """Нормализация данных формы без записи лишних символов."""

    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:max_length]


def build_site_application_message(
    application_id: str,
    name: str,
    phone: str,
    service: str,
    patient_message: str,
) -> str:
    """Текст заявки для Telegram и электронной почты."""

    message = (
        "🌐 НОВАЯ ЗАЯВКА С САЙТА\n\n"
        f"👤 Имя: {name}\n"
        f"📞 Телефон: {phone}\n"
        f"🩺 Услуга: {service or 'Не указана'}\n"
    )

    if patient_message:
        message += f"\n💬 Сообщение:\n{patient_message}\n"

    return (
        f"{message}\n──────────────\n"
        f"Номер заявки: {application_id}\n"
        "Источник: doctorgulnaz.ru"
    )


def send_application_email(
    application_id: str,
    name: str,
    application_text: str,
) -> None:
    """Отправка заявки через Gmail SMTP."""

    gmail_user = os.getenv("GMAIL_USER", "").strip()
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    gmail_to = os.getenv("GMAIL_TO", gmail_user).strip()

    if not gmail_user or not gmail_password or not gmail_to:
        raise RuntimeError("Переменные Gmail в Railway ещё не настроены.")

    email = EmailMessage()
    email["Subject"] = f"Новая заявка с сайта: {name} ({application_id})"
    email["From"] = gmail_user
    email["To"] = gmail_to
    email.set_content(application_text)

    smtp_context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        context=smtp_context,
        timeout=20,
    ) as smtp:
        smtp.login(gmail_user, gmail_password)
        smtp.send_message(email)


async def health(request: web.Request) -> web.Response:
    """Проверка доступности обработчика Railway."""

    return web.json_response(
        {
            "ok": True,
            "telegram_configured": bool(ADMIN_CHAT_ID),
            "gmail_configured": bool(
                os.getenv("GMAIL_USER") and os.getenv("GMAIL_APP_PASSWORD")
            ),
        }
    )


async def application_options(request: web.Request) -> web.Response:
    """Предварительный CORS-запрос браузера."""

    origin = request.headers.get("Origin", "")
    headers = cors_headers(origin)
    if not headers:
        return web.Response(status=403)
    return web.Response(status=204, headers=headers)


async def receive_site_application(request: web.Request) -> web.Response:
    """Приём заявки с формы официального сайта."""

    origin = request.headers.get("Origin", "")
    headers = cors_headers(origin)
    if not headers:
        return web.json_response(
            {"ok": False, "message": "Источник запроса не разрешён."},
            status=403,
        )

    if rate_limit_exceeded(client_ip(request)):
        return web.json_response(
            {
                "ok": False,
                "message": "Слишком много заявок. Попробуйте немного позднее.",
            },
            status=429,
            headers=headers,
        )

    try:
        data = await request.json()
    except Exception:
        return web.json_response(
            {"ok": False, "message": "Некорректный формат заявки."},
            status=400,
            headers=headers,
        )

    if not isinstance(data, dict):
        return web.json_response(
            {"ok": False, "message": "Некорректные данные заявки."},
            status=400,
            headers=headers,
        )

    # Скрытое поле-ловушка: обычный посетитель его не заполняет.
    if clean_text(data.get("website"), 200):
        return web.json_response({"ok": True}, headers=headers)

    name = clean_text(data.get("name"), 120)
    phone = clean_text(data.get("phone"), 40)
    service = clean_text(data.get("service"), 120)
    patient_message = clean_text(data.get("message"), 1500)
    phone_digits = re.sub(r"\D", "", phone)

    if len(name) < 2:
        return web.json_response(
            {"ok": False, "message": "Укажите имя пациента."},
            status=400,
            headers=headers,
        )

    if len(phone_digits) < 10 or len(phone_digits) > 15:
        return web.json_response(
            {"ok": False, "message": "Проверьте номер телефона."},
            status=400,
            headers=headers,
        )

    application_id = secrets.token_hex(4).upper()
    application_text = build_site_application_message(
        application_id,
        name,
        phone,
        service,
        patient_message,
    )

    telegram_sent = False
    email_sent = False

    try:
        await request.app["telegram_application"].bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=application_text,
        )
        telegram_sent = True
    except Exception as error:
        print("Ошибка отправки заявки сайта в Telegram:", type(error).__name__)

    try:
        send_application_email(
            application_id,
            name,
            application_text,
        )
        email_sent = True
    except Exception as error:
        print("Ошибка отправки заявки сайта в Gmail:", type(error).__name__)

    if not telegram_sent and not email_sent:
        return web.json_response(
            {
                "ok": False,
                "message": "Заявка временно не отправлена. Попробуйте позднее.",
            },
            status=502,
            headers=headers,
        )

    return web.json_response(
        {
            "ok": True,
            "application_id": application_id,
            "telegram_sent": telegram_sent,
            "email_sent": email_sent,
        },
        headers=headers,
    )


async def start_web_server(application: Application) -> None:
    """Запуск HTTP-обработчика вместе с Telegram-ботом."""

    web_application = web.Application(client_max_size=16 * 1024)
    web_application["telegram_application"] = application
    web_application.router.add_get("/health", health)
    web_application.router.add_route(
        "OPTIONS",
        "/api/application",
        application_options,
    )
    web_application.router.add_post(
        "/api/application",
        receive_site_application,
    )

    runner = web.AppRunner(web_application)
    await runner.setup()

    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    application.bot_data["web_runner"] = runner
    print(f" Обработчик заявок сайта запущен на порту {port}")


async def stop_web_server(application: Application) -> None:
    """Корректная остановка HTTP-обработчика."""

    runner = application.bot_data.get("web_runner")
    if runner is not None:
        await runner.cleanup()


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    context.user_data.clear()

    if update.message is None:
        return

    await update.message.reply_text(
        "Здравствуйте! 👋\n\n"
        "Я виртуальный помощник врача Гузаировой.\n\n"
        "Я помогу Вам:\n"
        "• познакомиться с врачом;\n"
        "• узнать стоимость консультаций;\n"
        "• подготовиться к консультации;\n"
        "• записаться на приём.\n\n"
        "Пожалуйста, выберите нужный раздел.",
        reply_markup=main_keyboard,
    )


async def show_my_id(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if update.effective_chat is None or update.message is None:
        return

    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "🆔 Идентификатор этого Telegram-чата:\n\n"
        f"`{chat_id}`\n\n"
        "Сохраните этот номер. Он понадобится для отправки "
        "заявок администратору.",
        parse_mode="Markdown",
    )


def main() -> None:
    app = (
        Application.builder()
        .token(TOKEN)
        .post_init(start_web_server)
        .post_shutdown(stop_web_server)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", show_my_id))

    questionnaire_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(r"^📅 Запись на консультацию$"),
                start_questionnaire,
            )
        ],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_name,
                )
            ],
            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_age,
                )
            ],
            HEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_height,
                )
            ],
            WEIGHT: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_weight,
                )
            ],
            PHONE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_phone,
                )
            ],
            PREFERRED_TIME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_preferred_time,
                )
            ],
            COMPLAINTS: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_complaints,
                )
            ],
            CONFIRM_APPLICATION: [
                CallbackQueryHandler(
                    confirm_application,
                    pattern=r"^confirm_application:",
                )
            ],
        },
        fallbacks=[
            CommandHandler(
                "cancel",
                cancel_questionnaire,
            )
        ],
        allow_reentry=True,
    )

    app.add_handler(questionnaire_handler)

    message_reply_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                start_admin_reply,
                pattern=r"^admin_reply:\d+$",
            ),
            CallbackQueryHandler(
                start_patient_reply,
                pattern=r"^patient_reply$",
            ),
        ],
        states={
            ADMIN_REPLY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    send_admin_reply,
                )
            ],
            PATIENT_REPLY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    send_patient_reply,
                )
            ],
        },
        fallbacks=[
            CommandHandler(
                "cancel",
                cancel_message_reply,
            )
        ],
        allow_reentry=True,
    )

    app.add_handler(message_reply_handler)

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu,
        )
    )

    print("===================================")
    print(" DoctorGuzairovaBot запущен")
    print(" Версия 2.1")
    print(" Анкета пациента: 7 шагов")
    print(" Передача анкеты администратору подключена")
    print(" Ответ администратора пациенту подключён")
    print(" Ответ пациента администратору подключён")
    print(" Команда /myid подключена")
    print(" Заявки с сайта: Telegram + Gmail")
    print("===================================")

    app.run_polling()


if __name__ == "__main__":
    main()