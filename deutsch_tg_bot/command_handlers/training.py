from typing import cast

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from deutsch_tg_bot.command_handlers.stop import stop_command
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DEUTCH_LEVEL_TENSES, DeutschLevel, SentenceTypeProbabilities
from deutsch_tg_bot.situation_training.handler import (
    situation_training_handler,
    start_situation_selection,
)
from deutsch_tg_bot.translation_training.handler import translation_training_handler
from deutsch_tg_bot.user_session import SentenceTranslationState, TrainingType, UserSession
from deutsch_tg_bot.utils.handler_validation import check_handler_acces
from deutsch_tg_bot.utils.random_selector import BalancedRandomSelector

STORE_LEVEL = 1
SELECT_TRAINING_TYPE = 2
STORE_SENTENCE_CONSTRAINT = 3
TRAINING_SESSION = 4
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

# Training type display names
TRAINING_TYPE_NAMES = {
    TrainingType.TRANSLATION: "Переклад речень",
    TrainingType.SITUATION: "Рольова гра (ситуації)",
}


@check_handler_acces
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["session"] = None

    await update.message.reply_text(
        "Привіт! Я твій бот для вивчення німецької мови. Будь ласка, обери свій поточний рівень німецької:",
        reply_markup=get_deutsch_level_keyboard(),
    )

    return STORE_LEVEL


async def store_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None or context.user_data is None:
        raise ValueError("Invalid update")

    try:
        deutsch_level = DeutschLevel(update.message.text)
    except ValueError:
        await update.message.reply_text(
            "Обрано невірний рівень. Будь ласка, обери правильний рівень німецької з клавіатури.",
            reply_markup=get_deutsch_level_keyboard(),
        )
        return STORE_LEVEL

    user_session = UserSession(deutsch_level=deutsch_level)
    context.user_data["session"] = user_session

    # Ask for training type
    await update.message.reply_text(
        f"Чудово! Твій рівень німецької: <b>{deutsch_level.value}</b>\n\nОбери тип тренування:",
        reply_markup=get_training_type_keyboard(),
        parse_mode="HTML",
    )

    return SELECT_TRAINING_TYPE


async def select_training_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None or context.user_data is None:
        raise ValueError("Invalid update")

    selected_text = update.message.text.strip()

    # Find matching training type
    selected_type: TrainingType | None = None
    for training_type, name in TRAINING_TYPE_NAMES.items():
        if name == selected_text:
            selected_type = training_type
            break

    if selected_type is None:
        await update.message.reply_text(
            "Будь ласка, обери тип тренування з клавіатури:",
            reply_markup=get_training_type_keyboard(),
        )
        return SELECT_TRAINING_TYPE

    user_session = cast(UserSession, context.user_data["session"])

    if selected_type == TrainingType.SITUATION:
        await start_situation_selection(update, context)
        return TRAINING_SESSION
    elif selected_type == TrainingType.TRANSLATION:
        user_session.sentence_translation = SentenceTranslationState(
            random_tense_selector=BalancedRandomSelector(
                items=DEUTCH_LEVEL_TENSES[user_session.deutsch_level],
            ),
            random_sentence_type_selector=BalancedRandomSelector(
                items=list(SentenceTypeProbabilities.keys()),
                weights=list(SentenceTypeProbabilities.values()),
            ),
        )

    # Translation training - ask for sentence constraints
    if settings.DEV_SKIP_SENTENCE_CONSTRAINT:
        await update.message.reply_text(
            "Обрано переклад речень!\nВведи /next, щоб отримати перше завдання.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return TRAINING_SESSION

    await update.message.reply_text(
        "Обрано переклад речень!\n\n"
        "Чи хочеш ти додати додаткові правила для генерації речень? "
        "(наприклад, 'Речення має містити слово immer')\n\n"
        "Якщо так, введи правила. Якщо ні, просто введи /skip.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return STORE_SENTENCE_CONSTRAINT


async def store_sentence_constraint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None or context.user_data is None:
        raise ValueError("Invalid update")

    user_session = cast(UserSession, context.user_data["session"])
    assert user_session.sentence_translation is not None
    message_text = update.message.text.strip()

    if message_text and message_text != "/skip":
        user_session.sentence_translation.sentence_constraint = update.message.text.strip()
        await update.message.reply_text(
            f"Правила збережено: {user_session.sentence_translation.sentence_constraint}\n"
            "Введи /next, щоб отримати перше завдання."
        )
    else:
        await update.message.reply_text("Введи /next, щоб отримати перше завдання.")

    return TRAINING_SESSION


training_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_handler)],
    states={
        STORE_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, store_level)],
        SELECT_TRAINING_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, select_training_type)
        ],
        STORE_SENTENCE_CONSTRAINT: [
            CommandHandler("skip", store_sentence_constraint),
            MessageHandler(filters.TEXT & ~filters.COMMAND, store_sentence_constraint),
        ],
        TRAINING_SESSION: [
            translation_training_handler,
            situation_training_handler,
        ],
    },
    fallbacks=[CommandHandler("stop", stop_command)],
    allow_reentry=True,
)


def get_deutsch_level_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            DeutschLevel.A2.value,
            DeutschLevel.B1.value,
            DeutschLevel.B2.value,
        ],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=True,
        input_field_placeholder="Твій рівень німецької",
    )


def get_training_type_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [TRAINING_TYPE_NAMES[TrainingType.TRANSLATION]],
        [TRAINING_TYPE_NAMES[TrainingType.SITUATION]],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=True,
        input_field_placeholder="Тип тренування",
    )
