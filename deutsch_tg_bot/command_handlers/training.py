from typing import cast

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from deutsch_tg_bot.command_handlers.excercise import excercise_handler
from deutsch_tg_bot.command_handlers.stop import stop_command
from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.user_session import UserSession

STORE_LEVEL = 1
STORE_SENTENCE_CONSTRAINT = 2
NEW_EXERCISE = 3
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    context.user_data["session"] = UserSession()

    await update.message.reply_text(
        "Привіт! Я твій бот для вивчення німецької мови. Будь ласка, обери свій поточний рівень німецької:",
        reply_markup=_get_level_keyboard(),
    )

    return STORE_LEVEL


async def store_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    user_session = cast(UserSession, context.user_data["session"])

    try:
        user_session.level = DeutschLevel(update.message.text)
    except ValueError:
        await update.message.reply_text(
            "Обрано невірний рівень. Будь ласка, обери правильний рівень німецької з клавіатури.",
            reply_markup=_get_level_keyboard(),
        )
        return STORE_LEVEL

    await update.message.reply_text(
        f"Чудово! Твій рівень німецької встановлено на {user_session.level.value}.\n"
        "Чи хочеш ти додати додаткові правила для генерації речень? (наприклад, 'Речення має містити слово immer')\n"
        "Якщо так, введи правила. Якщо ні, просто введи /skip.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return STORE_SENTENCE_CONSTRAINT


async def store_sentence_constraint(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    user_session = cast(UserSession, context.user_data["session"])
    message_text = update.message.text.strip()

    if message_text and message_text != "/skip":
        user_session.sentence_constraint = update.message.text.strip()
        await update.message.reply_text(
            f"Правила збережено: {user_session.sentence_constraint}\n"
            "Введи /next, щоб отримати перше завдання."
        )
    else:
        await update.message.reply_text("Введи /next, щоб отримати перше завдання.")

    return NEW_EXERCISE


training_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_handler)],
    states={
        STORE_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, store_level)],
        STORE_SENTENCE_CONSTRAINT: [
            CommandHandler("skip", store_sentence_constraint),
            MessageHandler(filters.TEXT & ~filters.COMMAND, store_sentence_constraint),
        ],
        NEW_EXERCISE: [excercise_handler],
    },
    fallbacks=[CommandHandler("stop", stop_command)],
)


def _get_level_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [level.value for level in DeutschLevel],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=True,
        input_field_placeholder="Твій рівень німецької",
    )
