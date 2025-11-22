from rich import print as rprint
from telegram import ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.user_session import get_user_session, reset_user_session

STORE_LEVEL = 1
NEW_EXERCISE = 2
CHECK_ANSWER = 3
ANSWER_QUESTION = 4
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reset_user_session(update.message.from_user)

    await update.message.reply_text(
        "Hi! I'm your Deutsch learning bot. Please choose your current Deutsch level:",
        reply_markup=_get_level_keyboard(),
    )

    return STORE_LEVEL


async def store_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    user_session = get_user_session(user)

    try:
        user_session.level = DeutschLevel(update.message.text)
    except ValueError:
        await update.message.reply_text(
            "Invalid level selected. Please choose a valid Deutsch level from the keyboard.",
            reply_markup=_get_level_keyboard(),
        )
        return STORE_LEVEL

    await update.message.reply_text(
        f"Great! Your Deutsch level is set to {user_session.level.value}.\n"
        "Type /next to get your first exercise.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NEW_EXERCISE


async def new_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rprint("Generating new exercise...")
    await update.message.reply_text("Я читаю книгу.", parse_mode="Markdown")
    return CHECK_ANSWER


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_answer = update.message.text
    correct_answer = "I am reading a book."

    if user_answer.strip().lower() == correct_answer.strip().lower():
        await update.message.reply_text("Correct! 🎉\nDo you have some questions?")
    else:
        await update.message.reply_text(
            f"Incorrect. The correct answer is: {correct_answer}.\nDo you have some questions?"
        )

    return ANSWER_QUESTION


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_question = update.message.text
    await update.message.reply_text(
        f"You asked: {user_question}\n(Answering questions is not implemented yet.)"
    )
    return ANSWER_QUESTION


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Goodbye! To start again, type /start.")
    return END


excercises_handler = ConversationHandler(
    entry_points=[CommandHandler("next", new_exercise)],
    states={
        CHECK_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
        ANSWER_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_questions)],
    },
    fallbacks=[
        CommandHandler("stop", stop),
        CommandHandler("next", new_exercise),
    ],
    map_to_parent={END: END},
)


training_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_handler)],
    states={
        STORE_LEVEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, store_level)],
        NEW_EXERCISE: [excercises_handler],
    },
    fallbacks=[CommandHandler("stop", stop)],
)


def _get_level_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [level.value for level in DeutschLevel],
    ]
    return ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=True,
        input_field_placeholder="Your Deutsch level",
    )
