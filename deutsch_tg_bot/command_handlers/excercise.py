from typing import cast

from rich import print as rprint
from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from deutsch_tg_bot.ai.sentence_generator import generate_sentence
from deutsch_tg_bot.command_handlers.stop import stop_command
from deutsch_tg_bot.user_session import UserSession

CHECK_ANSWER = 4
ANSWER_QUESTION = 5
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


async def new_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_session = cast(UserSession, context.user_data["session"])
    rprint(f"Generating new exercise for level {user_session.level}...")
    new_sentence = generate_sentence(
        level=user_session.level,
        previous_sentences=user_session.conversation_history,
        optional_constraint=user_session.constraint,
    )
    user_session.conversation_history.append(new_sentence)
    await update.message.reply_text(new_sentence.sentence, parse_mode="Markdown")
    return CHECK_ANSWER


async def check_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_answer = update.message.text
    correct_answer = "I am reading a book."

    if user_answer.strip().lower() == correct_answer.strip().lower():
        await update.message.reply_text("Правильно! 🎉\nУ тебе є якісь питання?")
    else:
        await update.message.reply_text(
            f"Неправильно. Правильна відповідь: {correct_answer}.\nУ тебе є якісь питання?"
        )

    return ANSWER_QUESTION


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_question = update.message.text
    await update.message.reply_text(
        f"Ти запитав: {user_question}\n(Відповіді на питання ще не реалізовані.)"
    )
    return ANSWER_QUESTION


excercise_handler = ConversationHandler(
    entry_points=[CommandHandler("next", new_exercise)],
    states={
        CHECK_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_answer)],
        ANSWER_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_questions)],
    },
    fallbacks=[
        CommandHandler("stop", stop_command),
        CommandHandler("next", new_exercise),
    ],
    map_to_parent={END: END},
)
