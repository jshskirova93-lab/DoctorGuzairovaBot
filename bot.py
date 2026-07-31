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
        "Р—РґСЂР°РІСЃС‚РІСѓР№С‚Рµ! рџ‘‹\n\n"
        "РЇ РІРёСЂС‚СѓР°Р»СЊРЅС‹Р№ РїРѕРјРѕС‰РЅРёРє РІСЂР°С‡Р° Р“СѓР·Р°РёСЂРѕРІРѕР№.\n\n"
        "РЇ РїРѕРјРѕРіСѓ Р’Р°Рј:\n"
        "вЂў РїРѕР·РЅР°РєРѕРјРёС‚СЊСЃСЏ СЃ РІСЂР°С‡РѕРј;\n"
        "вЂў СѓР·РЅР°С‚СЊ СЃС‚РѕРёРјРѕСЃС‚СЊ РєРѕРЅСЃСѓР»СЊС‚Р°С†РёР№;\n"
        "вЂў РїРѕРґРіРѕС‚РѕРІРёС‚СЊСЃСЏ Рє РєРѕРЅСЃСѓР»СЊС‚Р°С†РёРё;\n"
        "вЂў Р·Р°РїРёСЃР°С‚СЊСЃСЏ РЅР° РїСЂРёС‘Рј.\n\n"
        "РџРѕР¶Р°Р»СѓР№СЃС‚Р°, РІС‹Р±РµСЂРёС‚Рµ РЅСѓР¶РЅС‹Р№ СЂР°Р·РґРµР».",
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
        "рџ†” РРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ СЌС‚РѕРіРѕ Telegram-С‡Р°С‚Р°:\n\n"
        f"`{chat_id}`\n\n"
        "РЎРѕС…СЂР°РЅРёС‚Рµ СЌС‚РѕС‚ РЅРѕРјРµСЂ. РћРЅ РїРѕРЅР°РґРѕР±РёС‚СЃСЏ РґР»СЏ РѕС‚РїСЂР°РІРєРё "
        "Р·Р°СЏРІРѕРє Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ.",
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
                    r"^(рџ“… Р—Р°РїРёСЃСЊ РЅР° РєРѕРЅСЃСѓР»СЊС‚Р°С†РёСЋ|"
                    r"рџ“… Р—Р°РїРёСЃСЊ|"
                    r"в–¶пёЏ РџСЂРѕРґРѕР»Р¶РёС‚СЊ)$"
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
    print(" DoctorGuzairovaBot Р·Р°РїСѓС‰РµРЅ")
    print(" Р’РµСЂСЃРёСЏ 1.8")
    print(" РђРЅРєРµС‚Р° РїР°С†РёРµРЅС‚Р°: 7 С€Р°РіРѕРІ")
    print(" РџРµСЂРµРґР°С‡Р° Р°РЅРєРµС‚С‹ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ РїРѕРґРєР»СЋС‡РµРЅР°")
    print(" РћС‚РІРµС‚ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂР° РїР°С†РёРµРЅС‚Сѓ РїРѕРґРєР»СЋС‡С‘РЅ")
    print(" РћС‚РІРµС‚ РїР°С†РёРµРЅС‚Р° Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ РїРѕРґРєР»СЋС‡С‘РЅ")
    print(" РљРѕРјР°РЅРґР° /myid РїРѕРґРєР»СЋС‡РµРЅР°")
    print("===================================")

    app.run_polling()


if __name__ == "__main__":
    main()
