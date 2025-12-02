from typing import cast

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
from deutsch_tg_bot.tg_progress import progress
from deutsch_tg_bot.user_session import UserSession

CHECK_TRANSLATION = 4
ANSWER_QUESTION = 5
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


async def new_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    user_session = cast(UserSession, context.user_data["session"])
    previous_sentences = user_session.sentences_history[: settings.PREVIOUS_SENTENCES_NUMBER]

    async with progress(update, "Генерую нове речення"):
        new_sentence = await ai.generate_sentence(
            level=user_session.level,
            previous_sentences=previous_sentences,
            optional_constraint=user_session.sentence_constraint,
        )

    user_session.sentences_history.append(new_sentence)
    sentence_number = len(user_session.sentences_history)
    message = (
        f"*{sentence_number}. Переклади речення:*\n{new_sentence.sentence}\n\n"
        f"*Час*: {new_sentence.tense.value}"
    )
    await update.message.reply_text(message, parse_mode="Markdown")
    return CHECK_TRANSLATION


async def check_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    user_session = cast(UserSession, context.user_data["session"])
    current_sentence = user_session.sentences_history[-1]
    user_answer = update.message.text

    async with progress(update, "Перевіряю переклад"):
        check_result = await ai.check_translation(current_sentence, user_answer)

    user_session.conversation_messages = check_result.messages

    corrected_sentence = translation_check_result_to_message(check_result)
    user_session.sentences_history[-1].is_translation_correct = corrected_sentence is None

    correct_answers_number = sum(
        1 for sentence in user_session.sentences_history if sentence.is_translation_correct is True
    )
    total_result_message = (
        f"*Загальний результат:* {correct_answers_number} з {len(user_session.sentences_history)}"
    )

    if corrected_sentence is None:
        message = (
            "Переклад правильний!\n\n"
            f"{total_result_message}\n\n"
            "Якщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
        )
    else:
        message = (
            f"{corrected_sentence}\n\n"
            f"{total_result_message}\n\n"
            "Якщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
        )

    await update.message.reply_text(message, parse_mode="Markdown")

    return ANSWER_QUESTION


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    user_session = cast(UserSession, context.user_data["session"])
    user_question = update.message.text.strip()

    async with progress(update, "Думаю над відповідю"):
        user_session.conversation_messages, ai_reply = await ai.answer_question(
            user_session.conversation_messages,
            user_question,
        )

    reply_message = (
        ai_reply,
        "Якщо у тебе є ще питання, задай їх. Або введи /next для наступного речення.",
    )

    await update.message.reply_text(reply_message, parse_mode="Markdown")
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


def translation_check_result_to_message(
    translation_check_result: ai.TranslationCheckResult,
) -> str | None:
    if translation_check_result.correct_translation is None:
        return None

    correct_translation = translation_check_result.correct_translation
    correct_translation = correct_translation.replace("<error>", "*").replace("</error>", "*")

    message = f"\n\n*Правильний переклад:*\n{correct_translation}"
    message += f"\n\n*Пояснення:*\n{translation_check_result.explanation}"
    return message
