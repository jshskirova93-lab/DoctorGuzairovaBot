import os
from dotenv import load_dotenv

load_dotenv()

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

try:
    from config import TOKEN as LOCAL_TOKEN
except ImportError:
    LOCAL_TOKEN = None

TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TOKEN") or LOCAL_TOKEN

if not TOKEN:
    raise RuntimeError(
        "Telegram bot token not found. "
        "Set BOT_TOKEN or TOKEN environment variable."
    )

from keyboards import main_keyboard
from handlers import (
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
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", show_my_id))

    questionnaire_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex(
                    "^(\U0001F4C5 \u0417\u0430\u043f\u0438\u0441\u044c \u043d\u0430 \u043a\u043e\u043d\u0441\u0443\u043b\u044c\u0442\u0430\u0446\u0438\u044e|"
                    "\U0001F4C5 \u0417\u0430\u043f\u0438\u0441\u044c|"
                    "\u25b6\ufe0f \u041f\u0440\u043e\u0434\u043e\u043b\u0436\u0438\u0442\u044c)$"
                ),
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
    print(" Версия 1.9")
    print(" Анкета пациента: 7 шагов")
    print(" Передача анкеты администратору подключена")
    print(" Ответ администратора пациенту подключён")
    print(" Ответ пациента администратору подключён")
    print(" Команда /myid подключена")
    print("===================================")

    app.run_polling()


if __name__ == "__main__":
    main()