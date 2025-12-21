from typing import cast

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from deutsch_tg_bot.ai.question_answering import answer_question_with_ai
from deutsch_tg_bot.ai.sentence_generator import (
    SentenceGeneratorParams,
    generate_sentence_with_ai,
    get_random_tense_for_level,
    get_sentence_generator_params,
)
from deutsch_tg_bot.ai.translation_evalution import (
    TranslationEvaluationResult,
    evaluate_translation_with_ai,
)
from deutsch_tg_bot.command_handlers.stop import stop_command
from deutsch_tg_bot.tg_progress import progress
from deutsch_tg_bot.user_session import UserSession

CHECK_TRANSLATION = 4
ANSWER_QUESTION = 5
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


async def new_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    if context.user_data is None:
        raise ValueError("Expected user_data in context")
    user_session = cast(UserSession, context.user_data["session"])

    if user_session.level is None:
        raise ValueError("Expected level in user_session")

    sentence_generator_params = get_sentence_generator_params(
        level=user_session.level,
        tense=get_random_tense_for_level(user_session.level),
        sentences_history=user_session.sentences_history,
        optional_constraint=user_session.sentence_constraint,
    )

    progress_message = get_new_sentence_progress_message(sentence_generator_params)
    async with progress(update, progress_message):
        new_sentence = await generate_sentence_with_ai(sentence_generator_params)

    user_session.sentences_history.append(new_sentence)
    sentence_number = len(user_session.sentences_history)
    message = (
        f"<b>{sentence_number}. Переклади речення:</b>\n{new_sentence.ukrainian_sentence}\n\n"
        f"<b>Час</b>: {new_sentence.tense.value}"
    )
    await update.message.reply_text(message, parse_mode="HTML")
    return CHECK_TRANSLATION


def get_new_sentence_progress_message(sentence_generator_params: SentenceGeneratorParams) -> str:
    topic = sentence_generator_params["sentence_theme_topic"]
    if topic:
        return f'Генерую речення на тему "{topic}"'
    return "Генерую речення"


async def check_translation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    if context.user_data is None:
        raise ValueError("Expected user_data in context")

    user_session = cast(UserSession, context.user_data["session"])
    current_sentence = user_session.sentences_history[-1]
    user_answer = update.message.text

    async with progress(update, "Перевіряю переклад"):
        check_result = await evaluate_translation_with_ai(current_sentence, user_answer)

    user_session.last_translation_check_result = check_result
    user_session.sentences_history[-1].is_translation_correct = check_result.is_translation_correct
    user_session.sentences_history[-1].german_sentence = check_result.correct_translation

    correct_answers_number = sum(
        1 for sentence in user_session.sentences_history if sentence.is_translation_correct is True
    )
    total_result_message = (
        f"<b>Загальний результат:</b> {correct_answers_number}"
        f" з {len(user_session.sentences_history)}"
    )

    if check_result.is_translation_correct:
        message = (
            "Переклад правильний!\n\n"
            f"{total_result_message}\n\n"
            "Якщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
        )
    else:
        message = (
            f"{translation_check_result_to_message(check_result)}\n\n"
            f"{total_result_message}\n\n"
            "Якщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
        )

    await update.message.reply_text(message, parse_mode="HTML")

    return ANSWER_QUESTION


async def answer_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    if context.user_data is None:
        raise ValueError("Expected user_data in context")

    user_session = cast(UserSession, context.user_data["session"])
    if user_session.last_translation_check_result is None:
        raise ValueError("Expected last_translation_check_result to be initialized")

    user_question = update.message.text.strip()

    current_sentence = user_session.sentences_history[-1]

    async with progress(update, "Думаю над відповідю"):
        ai_reply, user_session.genai_chat = await answer_question_with_ai(
            user_question,
            current_sentence,
            user_session.last_translation_check_result,
            user_session.genai_chat,
        )

    message = (
        f"{ai_reply}\n\nЯкщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
    )

    await update.message.reply_text(message, parse_mode="HTML")
    return ANSWER_QUESTION


excercise_handler = ConversationHandler(
    entry_points=[CommandHandler("next", new_exercise)],
    states={
        CHECK_TRANSLATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_translation)],
        ANSWER_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_questions)],
    },
    fallbacks=[
        CommandHandler("stop", stop_command),
    ],
    map_to_parent={END: END},
    allow_reentry=True,
)


def translation_check_result_to_message(
    translation_check_result: TranslationEvaluationResult,
) -> str | None:
    if translation_check_result.correct_translation is None:
        return None

    correct_translation = translation_check_result.correct_translation
    # correct_translation = correct_translation.replace("<error>", "*").replace("</error>", "*")

    message = f"\n\n<b>Правильний переклад:</b>\n{correct_translation}"
    message += f"\n\n<b>Пояснення:</b>\n{translation_check_result.explanation}"
    return message
