import re

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
if not ADMIN_CHAT_ID:
    raise RuntimeError("Не задана переменная окружения ADMIN_CHAT_ID.")
ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)

from texts import (
    ABOUT_DOCTOR,
    TREATMENT_DIRECTIONS,
    REVIEWS_TEXT,
    CONTACTS_TEXT,
    WEBSITE_TEXT,
    PREPARATION_TEXT,
    FIRST_CONSULTATION,
    SECOND_CONSULTATION,
    EXPRESS_CONSULTATION,
)

from keyboards import (
    main_keyboard,
    price_keyboard,
    preparation_keyboard,
)


# Состояния анкеты пациента
NAME, AGE, HEIGHT, WEIGHT, PHONE, PREFERRED_TIME, COMPLAINTS, CONFIRM_APPLICATION = range(8)

# Состояния переписки через бота
ADMIN_REPLY, PATIENT_REPLY = range(100, 102)


def admin_reply_keyboard(
    patient_id: int,
) -> InlineKeyboardMarkup:
    """Кнопка ответа пациенту для администратора."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✉️ Ответить пациенту",
                    callback_data=f"admin_reply:{patient_id}",
                )
            ]
        ]
    )



def reviews_keyboard() -> InlineKeyboardMarkup:
    """Кнопка перехода к отзывам на портале ПроДокторов."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔗 Посмотреть отзывы на ПроДокторов",
                    url=(
                        "https://prodoctorov.ru/uchaly/"
                        "vrach/851468-guzairova/"
                    ),
                )
            ]
        ]
    )



def contacts_keyboard() -> InlineKeyboardMarkup:
    """Кнопка для связи через Telegram."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✈️ Написать в Telegram",
                    url="https://t.me/DoctorGuzairovaBot",
                )
            ]
        ]
    )



def website_keyboard() -> InlineKeyboardMarkup:
    """Кнопка перехода на официальный сайт."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🌐 Открыть официальный сайт",
                    url="http://online.tabib102.ru",
                )
            ]
        ]
    )


def patient_reply_keyboard() -> InlineKeyboardMarkup:
    """Кнопка ответа администратору для пациента."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✉️ Ответить администратору",
                    callback_data="patient_reply",
                )
            ]
        ]
    )


async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Обработка кнопок главного меню."""

    if update.message is None or update.message.text is None:
        return

    text = update.message.text.strip()

    if text.endswith("О докторе"):
        await update.message.reply_text(
            ABOUT_DOCTOR,
            reply_markup=main_keyboard,
        )

    elif text.endswith("Направления лечения"):
        await update.message.reply_text(
            TREATMENT_DIRECTIONS,
            reply_markup=main_keyboard,
        )

    elif text.endswith("Стоимость услуг"):
        await update.message.reply_text(
            "Выберите интересующую консультацию:",
            reply_markup=price_keyboard,
        )

    elif text == "🩺 Первичная консультация":
        await update.message.reply_text(
            FIRST_CONSULTATION,
            reply_markup=price_keyboard,
        )

    elif text == "🔄 Повторная консультация":
        await update.message.reply_text(
            SECOND_CONSULTATION,
            reply_markup=price_keyboard,
        )

    elif text == "⚡ Экспресс-консультация":
        await update.message.reply_text(
            EXPRESS_CONSULTATION,
            reply_markup=price_keyboard,
        )

    elif text in ("🔙 Назад", "🔙 Главное меню"):
        await update.message.reply_text(
            "Главное меню",
            reply_markup=main_keyboard,
        )

    elif text.endswith("Подготовка к консультации"):
        await update.message.reply_text(
            PREPARATION_TEXT,
            reply_markup=preparation_keyboard,
        )

    elif text.endswith("Запись на консультацию") or text == "📅 Запись":
        await update.message.reply_text(
            "Для записи воспользуйтесь кнопкой "
            "«📅 Запись на консультацию».",
            reply_markup=main_keyboard,
        )

    elif text.endswith("Отзывы"):
        await update.message.reply_text(
            REVIEWS_TEXT,
            reply_markup=reviews_keyboard(),
        )

    elif text.endswith("Контакты"):
        await update.message.reply_text(
            CONTACTS_TEXT,
            reply_markup=contacts_keyboard(),
        )

    elif text.endswith("Сайт"):
        await update.message.reply_text(
            WEBSITE_TEXT,
            reply_markup=website_keyboard(),
        )


    else:
        await update.message.reply_text(
            "Пожалуйста, воспользуйтесь кнопками меню.",
            reply_markup=main_keyboard,
        )


async def start_questionnaire(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Начало анкеты пациента."""

    if update.message is None:
        return ConversationHandler.END

    context.user_data.clear()

    await update.message.reply_text(
        "📋 Начинаем предварительную анкету пациента.\n\n"
        "Заполнение анкеты можно отменить командой /cancel.\n\n"
        "Шаг 1 из 7\n\n"
        "Напишите Ваши фамилию, имя и отчество.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return NAME


async def receive_name(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Получение ФИО пациента."""

    if update.message is None or update.message.text is None:
        return NAME

    name = update.message.text.strip()

    if len(name) < 3:
        await update.message.reply_text(
            "Пожалуйста, укажите фамилию, имя и отчество."
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        "Шаг 2 из 7\n\n"
        "Сколько Вам полных лет?\n\n"
        "Введите возраст числом, например: 52"
    )

    return AGE


async def receive_age(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Получение возраста пациента."""

    if update.message is None or update.message.text is None:
        return AGE

    text = update.message.text.strip()

    try:
        age = int(text)
    except ValueError:
        await update.message.reply_text(
            "Возраст нужно указать целым числом.\n"
            "Например: 52"
        )
        return AGE

    if age < 18 or age > 120:
        await update.message.reply_text(
            "Пожалуйста, укажите возраст от 18 до 120 лет."
        )
        return AGE

    context.user_data["age"] = age

    await update.message.reply_text(
        "Шаг 3 из 7\n\n"
        "Укажите Ваш рост в сантиметрах.\n\n"
        "Например: 168"
    )

    return HEIGHT


async def receive_height(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Получение роста пациента."""

    if update.message is None or update.message.text is None:
        return HEIGHT

    text = update.message.text.strip().replace(",", ".")

    try:
        height = float(text)
    except ValueError:
        await update.message.reply_text(
            "Рост нужно указать числом в сантиметрах.\n"
            "Например: 168"
        )
        return HEIGHT

    if height < 100 or height > 230:
        await update.message.reply_text(
            "Пожалуйста, укажите рост от 100 до 230 см."
        )
        return HEIGHT

    context.user_data["height"] = height

    await update.message.reply_text(
        "Шаг 4 из 7\n\n"
        "Укажите Ваш вес в килограммах.\n\n"
        "Например: 74 или 74,5"
    )

    return WEIGHT


async def receive_weight(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Получение веса пациента."""

    if update.message is None or update.message.text is None:
        return WEIGHT

    text = update.message.text.strip().replace(",", ".")

    try:
        weight = float(text)
    except ValueError:
        await update.message.reply_text(
            "Вес нужно указать числом.\n"
            "Например: 74 или 74,5"
        )
        return WEIGHT

    if weight < 30 or weight > 350:
        await update.message.reply_text(
            "Пожалуйста, укажите вес от 30 до 350 кг."
        )
        return WEIGHT

    context.user_data["weight"] = weight

    await update.message.reply_text(
        "Шаг 5 из 7\n\n"
        "Укажите номер телефона для связи с Вами.\n\n"
        "Например: +7 917 123-45-67"
    )

    return PHONE


async def receive_phone(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Получение номера телефона пациента."""

    if update.message is None or update.message.text is None:
        return PHONE

    phone = update.message.text.strip()
    digits = re.sub(r"\D", "", phone)

    if len(digits) < 10 or len(digits) > 15:
        await update.message.reply_text(
            "Пожалуйста, проверьте номер телефона.\n\n"
            "Он должен содержать от 10 до 15 цифр.\n"
            "Например: +7 917 123-45-67"
        )
        return PHONE

    context.user_data["phone"] = phone

    await update.message.reply_text(
        "Шаг 6 из 7\n\n"
        "Укажите желаемую дату и удобное время консультации.\n\n"
        "Например:\n"
        "25 июля после 15:00\n"
        "или\n"
        "В любой будний день утром"
    )

    return PREFERRED_TIME


async def receive_preferred_time(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Получение желаемой даты и времени консультации."""

    if update.message is None or update.message.text is None:
        return PREFERRED_TIME

    preferred_time = update.message.text.strip()

    if len(preferred_time) < 3:
        await update.message.reply_text(
            "Пожалуйста, укажите желаемую дату "
            "или удобное время консультации."
        )
        return PREFERRED_TIME

    context.user_data["preferred_time"] = preferred_time

    await update.message.reply_text(
        "Шаг 7 из 7\n\n"
        "Опишите основную жалобу или проблему, "
        "с которой Вы обращаетесь к врачу.\n\n"
        "Можно написать несколько предложений."
    )

    return COMPLAINTS


def application_confirm_keyboard() -> InlineKeyboardMarkup:
    """Кнопки подтверждения анкеты пациентом."""

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Отправить заявку",
                    callback_data="confirm_application:send",
                )
            ],
            [
                InlineKeyboardButton(
                    "✏️ Заполнить заново",
                    callback_data="confirm_application:restart",
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Отменить",
                    callback_data="confirm_application:cancel",
                )
            ],
        ]
    )


def build_application_messages(
    context: ContextTypes.DEFAULT_TYPE,
    user,
) -> tuple[str, str, int | None]:
    """Формирование текста анкеты для администратора и пациента."""

    name = context.user_data.get("name", "Не указано")
    age = context.user_data.get("age", "Не указан")
    height = context.user_data.get("height")
    weight = context.user_data.get("weight")
    phone = context.user_data.get("phone", "Не указан")
    preferred_time = context.user_data.get(
        "preferred_time",
        "Не указано",
    )
    complaints = context.user_data.get("complaints", "Не указано")

    if isinstance(height, (int, float)):
        height_text = f"{height:g}"
    else:
        height_text = "Не указан"

    if isinstance(weight, (int, float)):
        weight_text = f"{weight:g}"
    else:
        weight_text = "Не указан"

    if user is not None:
        telegram_id = user.id
        patient_first_name = user.first_name or "Не указано"
        patient_last_name = user.last_name or ""

        if user.username:
            telegram_username = f"@{user.username}"
        else:
            telegram_username = "Не указан"
    else:
        telegram_id = None
        telegram_username = "Не указан"
        patient_first_name = "Не указано"
        patient_last_name = ""

    telegram_name = (
        f"{patient_first_name} {patient_last_name}"
    ).strip()

    admin_message = (
        "🆕 НОВАЯ АНКЕТА ПАЦИЕНТА\n\n"
        f"👤 ФИО: {name}\n"
        f"🎂 Возраст: {age} лет\n"
        f"📏 Рост: {height_text} см\n"
        f"⚖️ Вес: {weight_text} кг\n"
        f"📞 Телефон: {phone}\n"
        f"📅 Желаемая дата и время: {preferred_time}\n\n"
        "🩺 Основная жалоба:\n"
        f"{complaints}\n\n"
        "──────────────\n"
        f"Имя в Telegram: {telegram_name}\n"
        f"Telegram: {telegram_username}\n"
        f"Telegram ID: {telegram_id or 'Не определён'}"
    )

    patient_message = (
        "Пожалуйста, проверьте данные анкеты перед отправкой.\n\n"
        f"ФИО: {name}\n"
        f"Возраст: {age} лет\n"
        f"Рост: {height_text} см\n"
        f"Вес: {weight_text} кг\n"
        f"Телефон: {phone}\n"
        f"Желаемая дата и время: {preferred_time}\n"
        f"Основная жалоба: {complaints}\n\n"
        "Если всё верно, нажмите «✅ Отправить заявку». "
        "Если нужно исправить данные, нажмите «✏️ Заполнить заново»."
    )

    return admin_message, patient_message, telegram_id


async def receive_complaints(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Получение жалобы и показ анкеты пациенту для подтверждения."""

    if update.message is None or update.message.text is None:
        return COMPLAINTS

    complaints = update.message.text.strip()

    if len(complaints) < 5:
        await update.message.reply_text(
            "Пожалуйста, опишите жалобу немного подробнее."
        )
        return COMPLAINTS

    context.user_data["complaints"] = complaints

    _, patient_message, _ = build_application_messages(
        context,
        update.effective_user,
    )

    await update.message.reply_text(
        patient_message,
        reply_markup=application_confirm_keyboard(),
    )

    return CONFIRM_APPLICATION


async def confirm_application(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Подтверждение, повторное заполнение или отмена анкеты."""

    query = update.callback_query

    if query is None:
        return CONFIRM_APPLICATION

    await query.answer()

    if query.data == "confirm_application:restart":
        context.user_data.clear()

        if query.message is not None:
            await query.message.reply_text(
                "Начнём заполнение анкеты заново.\n\n"
                "Шаг 1 из 7\n\n"
                "Введите, пожалуйста, Ваши фамилию, имя и отчество.",
                reply_markup=ReplyKeyboardRemove(),
            )

        return NAME

    if query.data == "confirm_application:cancel":
        context.user_data.clear()

        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

        if query.message is not None:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Заполнение анкеты отменено.",
                reply_markup=main_keyboard,
            )

        return ConversationHandler.END

    if query.data != "confirm_application:send":
        return CONFIRM_APPLICATION

    admin_message, patient_message, telegram_id = build_application_messages(
        context,
        update.effective_user,
    )

    try:
        if telegram_id is not None:
            reply_markup = admin_reply_keyboard(telegram_id)
        else:
            reply_markup = None

        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            reply_markup=reply_markup,
        )

    except Exception as error:
        print(
            "Ошибка отправки анкеты администратору:",
            error,
        )

        if query.message is not None:
            await query.message.reply_text(
                "⚠️ Анкета заполнена, но при её передаче "
                "администратору произошла ошибка.\n\n"
                "Пожалуйста, попробуйте позднее или свяжитесь "
                "с администратором другим способом.",
                reply_markup=main_keyboard,
            )

        context.user_data.clear()

        return ConversationHandler.END

    if query.message is not None:
        await query.message.reply_text(
            "✅ Ваша предварительная анкета заполнена "
            "и передана администратору.\n\n"
            f"{patient_message}\n\n"
            "Администратор ознакомится с информацией "
            "и свяжется с Вами для согласования консультации.",
            reply_markup=main_keyboard,
        )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel_questionnaire(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Отмена заполнения анкеты."""

    context.user_data.clear()

    if update.message is not None:
        await update.message.reply_text(
            "Заполнение анкеты отменено.",
            reply_markup=main_keyboard,
        )

    return ConversationHandler.END


async def start_admin_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Начало ответа администратора пациенту."""

    query = update.callback_query

    if query is None:
        return ConversationHandler.END

    if (
        update.effective_chat is None
        or update.effective_chat.id != ADMIN_CHAT_ID
    ):
        await query.answer(
            "Эта кнопка доступна только администратору.",
            show_alert=True,
        )
        return ConversationHandler.END

    await query.answer()

    callback_data = query.data or ""

    try:
        patient_id = int(callback_data.split(":", 1)[1])
    except (IndexError, ValueError):
        if query.message is not None:
            await query.message.reply_text(
                "Не удалось определить Telegram ID пациента."
            )

        return ConversationHandler.END

    context.user_data["reply_patient_id"] = patient_id

    if query.message is not None:
        await query.message.reply_text(
            "✍️ Напишите сообщение пациенту одним сообщением.\n\n"
            "Для отмены отправьте команду /cancel.",
            reply_markup=ReplyKeyboardRemove(),
        )

    return ADMIN_REPLY


async def send_admin_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Отправка сообщения администратора пациенту."""

    if (
        update.effective_chat is None
        or update.effective_chat.id != ADMIN_CHAT_ID
    ):
        return ConversationHandler.END

    if update.message is None or update.message.text is None:
        return ADMIN_REPLY

    message_text = update.message.text.strip()

    if len(message_text) < 1:
        await update.message.reply_text(
            "Введите текст сообщения пациенту."
        )
        return ADMIN_REPLY

    patient_id = context.user_data.get("reply_patient_id")

    if not isinstance(patient_id, int):
        await update.message.reply_text(
            "Не удалось определить пациента. "
            "Нажмите кнопку ответа ещё раз.",
            reply_markup=main_keyboard,
        )
        return ConversationHandler.END

    try:
        await context.bot.send_message(
            chat_id=patient_id,
            text=(
                "💬 Сообщение от администратора "
                "доктора Гузаировой\n\n"
                f"{message_text}"
            ),
            reply_markup=patient_reply_keyboard(),
        )

    except Exception as error:
        print(
            "Ошибка отправки сообщения пациенту:",
            error,
        )

        await update.message.reply_text(
            "⚠️ Сообщение не отправлено.\n\n"
            "Возможно, пациент заблокировал бота "
            "или удалил переписку с ним.",
            reply_markup=main_keyboard,
        )

        context.user_data.pop(
            "reply_patient_id",
            None,
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Сообщение отправлено пациенту.",
        reply_markup=main_keyboard,
    )

    context.user_data.pop(
        "reply_patient_id",
        None,
    )

    return ConversationHandler.END


async def start_patient_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Начало ответа пациента администратору."""

    query = update.callback_query

    if query is None:
        return ConversationHandler.END

    await query.answer()

    if query.message is not None:
        await query.message.reply_text(
            "✍️ Напишите Ваш ответ администратору "
            "одним сообщением.\n\n"
            "Для отмены отправьте команду /cancel.",
            reply_markup=ReplyKeyboardRemove(),
        )

    return PATIENT_REPLY


async def send_patient_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Отправка ответа пациента администратору."""

    if update.message is None or update.message.text is None:
        return PATIENT_REPLY

    message_text = update.message.text.strip()

    if len(message_text) < 1:
        await update.message.reply_text(
            "Введите текст сообщения администратору."
        )
        return PATIENT_REPLY

    user = update.effective_user

    if user is None:
        await update.message.reply_text(
            "Не удалось определить отправителя сообщения.",
            reply_markup=main_keyboard,
        )
        return ConversationHandler.END

    patient_id = user.id
    patient_first_name = user.first_name or "Не указано"
    patient_last_name = user.last_name or ""

    patient_name = (
        f"{patient_first_name} {patient_last_name}"
    ).strip()

    if user.username:
        telegram_username = f"@{user.username}"
    else:
        telegram_username = "Не указан"

    admin_message = (
        "💬 НОВОЕ СООБЩЕНИЕ ОТ ПАЦИЕНТА\n\n"
        f"Имя в Telegram: {patient_name}\n"
        f"Telegram: {telegram_username}\n"
        f"Telegram ID: {patient_id}\n\n"
        "Сообщение:\n"
        f"{message_text}"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            reply_markup=admin_reply_keyboard(patient_id),
        )

    except Exception as error:
        print(
            "Ошибка отправки сообщения администратору:",
            error,
        )

        await update.message.reply_text(
            "⚠️ Сообщение не удалось передать администратору.\n"
            "Пожалуйста, попробуйте позднее.",
            reply_markup=main_keyboard,
        )

        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Ваше сообщение передано администратору.",
        reply_markup=main_keyboard,
    )

    return ConversationHandler.END


async def cancel_message_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Отмена отправки сообщения."""

    context.user_data.pop(
        "reply_patient_id",
        None,
    )

    if update.message is not None:
        await update.message.reply_text(
            "Отправка сообщения отменена.",
            reply_markup=main_keyboard,
        )

    return ConversationHandler.END