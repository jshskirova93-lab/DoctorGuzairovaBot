from telegram import ReplyKeyboardMarkup


main_keyboard = ReplyKeyboardMarkup(
    [
        ["👩‍⚕️ О докторе", "🩺 Направления лечения"],
        ["💰 Стоимость услуг", "📅 Запись на консультацию"],
        ["📋 Подготовка к консультации", "⭐ Отзывы"],
        ["📍 Контакты"],
        ["🌐 Сайт"],
    ],
    resize_keyboard=True,
)


price_keyboard = ReplyKeyboardMarkup(
    [
        ["🩺 Первичная консультация"],
        ["🔄 Повторная консультация"],
        ["⚡ Экспресс-консультация"],
        ["🔙 Назад"],
    ],
    resize_keyboard=True,
)


preparation_keyboard = ReplyKeyboardMarkup(
    [
        ["▶️ Продолжить"],
        ["🔙 Главное меню"],
    ],
    resize_keyboard=True,
)