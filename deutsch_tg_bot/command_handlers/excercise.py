from email import message
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

from deutsch_tg_bot import ai
from deutsch_tg_bot.command_handlers.stop import stop_command
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.user_session import UserSession

CHECK_TRANSLATION = 4
ANSWER_QUESTION = 5
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


async def new_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    # await update.message.reply_text("_Генерую нове речення..._", parse_mode="Markdown")

    user_session = cast(UserSession, context.user_data["session"])
    previous_sentences = user_session.sentences_history[: settings.PREVIOUS_SENTENCES_NUMBER]
    new_sentence = ai.generate_sentence(
        level=user_session.level,
        previous_sentences=previous_sentences,
        optional_constraint=user_session.sentence_constraint,
    )
    user_session.sentences_history.append(new_sentence)
    message = f"*Переклади речення:*\n{new_sentence.sentence}\n\n*Час*: {new_sentence.tense.value}"
    await update.message.reply_text(message, parse_mode="Markdown")
    return CHECK_TRANSLATION


async def check_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    # await update.message.reply_text("_Перевіряю переклад..._", parse_mode="Markdown")

    user_session = cast(UserSession, context.user_data["session"])
    current_sentence = user_session.sentences_history[-1]
    user_answer = update.message.text
    check_result = ai.check_translation(current_sentence, user_answer)
    user_session.conversation_messages = check_result.messages

    message = translation_check_result_to_message(check_result)
    await update.message.reply_text(message, parse_mode="Markdown")

    return ANSWER_QUESTION


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    # await update.message.reply_text("_Думаю над відповідю..._", parse_mode="Markdown")

    user_session = cast(UserSession, context.user_data["session"])
    user_question = update.message.text.strip()
    user_session.conversation_messages, ai_reply = ai.answer_question(
        user_session.conversation_messages,
        user_question,
    )

    await update.message.reply_text(ai_reply, parse_mode="Markdown")
    return ANSWER_QUESTION


excercise_handler = ConversationHandler(
    entry_points=[CommandHandler("next", new_exercise)],
    states={
        CHECK_TRANSLATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_translation)],
        ANSWER_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_questions)],
    },
    fallbacks=[
        CommandHandler("stop", stop_command),
        CommandHandler("next", new_exercise),
    ],
    map_to_parent={END: END},
)


def translation_check_result_to_message(translation_check_result: ai.TranslationCheckResult) -> str:
    if translation_check_result.correct_translation is None:
        return "Все вірно! Твій переклад правильний.\n\nУ тебе є якісь питання?"

    message = f"\n\n*Правильний переклад:*\n{translation_check_result.correct_translation}"
    message += f"\n\n*Пояснення:*\n{translation_check_result.explanation}"
    message += "\n\nУ тебе є якісь питання?"
    return message
