"""ConversationHandler for translation training exercises."""

import asyncio

from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from deutsch_tg_bot.command_handlers.stop import stop_command
from deutsch_tg_bot.data_types import Sentence
from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.tg_progress import progress
from deutsch_tg_bot.translation_training.ai.question_answering import answer_question_with_ai
from deutsch_tg_bot.translation_training.ai.sentence_generator import (
    generate_sentence_with_ai,
    get_sentence_generator_params,
)
from deutsch_tg_bot.translation_training.ai.translation_evaluation import (
    TranslationEvaluationResult,
    evaluate_translation_with_ai,
)
from deutsch_tg_bot.user_session import SentenceTranslationState
from deutsch_tg_bot.utils.handler_validation import ValidatedUpdate, check_handler_acces

CHECK_TRANSLATION = 4
ANSWER_QUESTION = 5
# Shortcut for ConversationHandler.END
END = ConversationHandler.END


@check_handler_acces
async def new_exercise(vu: ValidatedUpdate) -> int:
    sentence_translation = vu.session.sentence_translation
    assert sentence_translation is not None

    if sentence_translation.new_sentence_generation_task is None:
        sentence_translation.new_sentence_generation_task = asyncio.create_task(
            _generate_new_sentence(vu.session.deutsch_level, sentence_translation)
        )

    if not sentence_translation.new_sentence_generation_task.done():
        async with progress(vu, "Генерую нове речення"):
            await asyncio.wait([sentence_translation.new_sentence_generation_task])

    new_sentence = sentence_translation.new_sentence_generation_task.result()
    sentence_translation.sentences_history.append(new_sentence)
    sentence_number = len(sentence_translation.sentences_history)
    message = (
        f"<b>{sentence_number}. Переклади речення:</b>\n{new_sentence.ukrainian_sentence}\n\n"
        f"<b>Час</b>: {new_sentence.tense.value}"
    )
    await vu.message.reply_text(message, parse_mode="HTML")

    sentence_translation.new_sentence_generation_task = asyncio.create_task(
        _generate_new_sentence(vu.session.deutsch_level, sentence_translation)
    )
    return CHECK_TRANSLATION


async def _generate_new_sentence(
    deutsch_level: DeutschLevel, sentence_translation: SentenceTranslationState
) -> Sentence:
    random_tense_selector = sentence_translation.random_tense_selector
    random_sentence_type_selector = sentence_translation.random_sentence_type_selector

    sentence_generator_params = get_sentence_generator_params(
        level=deutsch_level,
        tense=random_tense_selector.select(),
        sentence_type=random_sentence_type_selector.select(),
        sentences_history=sentence_translation.sentences_history,
        optional_constraint=sentence_translation.sentence_constraint,
    )
    new_sentence = await generate_sentence_with_ai(sentence_generator_params)
    return new_sentence


@check_handler_acces
async def check_translation(vu: ValidatedUpdate) -> int:
    sentence_translation = vu.session.sentence_translation
    assert sentence_translation is not None

    current_sentence = sentence_translation.sentences_history[-1]

    async with progress(vu, "Перевіряю переклад"):
        check_result = await evaluate_translation_with_ai(current_sentence, vu.message_text)

    sentence_translation.last_translation_check_result = check_result
    sentence_translation.sentences_history[
        -1
    ].is_translation_correct = check_result.is_translation_correct
    sentence_translation.sentences_history[-1].german_sentence = check_result.correct_translation

    correct_answers_number = sum(
        1
        for sentence in sentence_translation.sentences_history
        if sentence.is_translation_correct is True
    )
    total_result_message = (
        f"<b>Загальний результат:</b> {correct_answers_number}"
        f" з {len(sentence_translation.sentences_history)}"
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

    await vu.message.reply_text(message, parse_mode="HTML")
    return ANSWER_QUESTION


@check_handler_acces
async def answer_questions(vu: ValidatedUpdate) -> int:
    sentence_translation = vu.session.sentence_translation
    assert sentence_translation is not None

    if sentence_translation.last_translation_check_result is None:
        raise ValueError("Expected last_translation_check_result to be initialized")

    current_sentence = sentence_translation.sentences_history[-1]

    async with progress(vu, "Думаю над відповідю"):
        ai_reply, sentence_translation.genai_chat = await answer_question_with_ai(
            vu.message_text,
            current_sentence,
            sentence_translation.last_translation_check_result,
            sentence_translation.genai_chat,
        )

    message = (
        f"{ai_reply}\n\nЯкщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
    )

    await vu.message.reply_text(message, parse_mode="HTML")
    return ANSWER_QUESTION


translation_training_handler = ConversationHandler(
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

    message = f"\n\n<b>Правильний переклад:</b>\n{correct_translation}"
    message += f"\n\n<b>Пояснення:</b>\n{translation_check_result.explanation}"
    return message
