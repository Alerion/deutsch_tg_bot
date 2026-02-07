import asyncio
from tabnanny import check

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.data_types import Sentence
from deutsch_tg_bot.deutsh_enums import DEUTCH_LEVEL_TENSES, DeutschLevel, SentenceTypeProbabilities
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
from deutsch_tg_bot.utils.random_selector import BalancedRandomSelector


class TranslationTraining(StatesGroup):
    add_sentence_constraint = State()
    check_translation = State()
    answer_question = State()


router = Router()

# TODO: Add /next command handler


# @translation_training_router.message(Setup.select_training_type)
@router.callback_query(F.data == "select_training_type:translation")
async def select_training_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_text("Ти обрав тренування 'Переклад речень'")

    deutsch_level = await state.get_value("deutsch_level")
    sentence_translation = SentenceTranslationState(
        random_tense_selector=BalancedRandomSelector(
            items=DEUTCH_LEVEL_TENSES[deutsch_level],
        ),
        random_sentence_type_selector=BalancedRandomSelector(
            items=list(SentenceTypeProbabilities.keys()),
            weights=list(SentenceTypeProbabilities.values()),
        ),
    )
    await state.update_data(sentence_translation=sentence_translation)

    await state.set_state(TranslationTraining.add_sentence_constraint)
    await callback_query.message.answer(
        "Чи хочеш ти додати додаткові правила для генерації речень? "
        "(наприклад, 'Речення має містити слово immer')\n\n"
        "Якщо так, введи правила. Якщо ні, просто введи /skip.",
    )


@router.message(TranslationTraining.add_sentence_constraint)
@router.message(TranslationTraining.answer_question, Command("next"))
async def generate_new_sentence_to_translate(message: Message, state: FSMContext) -> None:
    sentence_translation: SentenceTranslationState = await state.get_value("sentence_translation")
    assert sentence_translation is not None

    # First sentence. Store sentence_constraint
    current_state = await state.get_state()
    if current_state == TranslationTraining.add_sentence_constraint:
        if message.text and message.text != "/skip":
            sentence_translation.sentence_constraint = message.text

    deutsch_level: DeutschLevel = await state.get_value("deutsch_level")
    if sentence_translation.new_sentence_generation_task is None:
        sentence_translation.new_sentence_generation_task = asyncio.create_task(
            _generate_new_sentence(deutsch_level, sentence_translation)
        )

    if not sentence_translation.new_sentence_generation_task.done():
        async with progress(message, "Генерую нове речення"):
            await asyncio.wait([sentence_translation.new_sentence_generation_task])

    new_sentence = sentence_translation.new_sentence_generation_task.result()
    sentence_translation.sentences_history.append(new_sentence)
    sentence_number = len(sentence_translation.sentences_history)
    answer_message = (
        f"<b>{sentence_number}. Переклади речення:</b>\n{new_sentence.ukrainian_sentence}\n\n"
        f"<b>Час</b>: {new_sentence.tense.value}"
    )
    await message.answer(answer_message, parse_mode="HTML")

    sentence_translation.new_sentence_generation_task = asyncio.create_task(
        _generate_new_sentence(deutsch_level, sentence_translation)
    )
    await state.set_state(TranslationTraining.check_translation)
    await state.update_data(sentence_translation=sentence_translation)


@router.message(TranslationTraining.check_translation)
async def check_translation(message: Message, state: FSMContext) -> None:
    sentence_translation: SentenceTranslationState = await state.get_value("sentence_translation")
    assert sentence_translation is not None

    current_sentence = sentence_translation.sentences_history[-1]

    async with progress(message, "Перевіряю переклад"):
        check_result = await evaluate_translation_with_ai(current_sentence, message.text)

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
        answer_message = (
            "Переклад правильний!\n\n"
            f"{total_result_message}\n\n"
            "Якщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
        )
    else:
        answer_message = (
            f"{_translation_check_result_to_message(check_result)}\n\n"
            f"{total_result_message}\n\n"
            "Якщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
        )

    await message.answer(answer_message)
    await state.set_state(TranslationTraining.answer_question)
    await state.update_data(sentence_translation=sentence_translation)


@router.message(TranslationTraining.answer_question)
async def answer_question(message: Message, state: FSMContext) -> None:
    sentence_translation: SentenceTranslationState = await state.get_value("sentence_translation")
    assert sentence_translation is not None

    if sentence_translation.last_translation_check_result is None:
        raise ValueError("Expected last_translation_check_result to be initialized")

    current_sentence = sentence_translation.sentences_history[-1]

    async with progress(message, "Думаю над відповідю"):
        ai_reply, sentence_translation.genai_chat = await answer_question_with_ai(
            message.text,
            current_sentence,
            sentence_translation.last_translation_check_result,
            sentence_translation.genai_chat,
        )

    answer_message = f"{html.code(ai_reply)}\n\nЯкщо у тебе є ще питання, задай їх. Або введи /next для наступного речення."
    await message.answer(answer_message)
    await state.update_data(sentence_translation=sentence_translation)


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


def _translation_check_result_to_message(
    translation_check_result: TranslationEvaluationResult,
) -> str | None:
    if translation_check_result.correct_translation is None:
        return None

    correct_translation = translation_check_result.correct_translation

    message = f"\n\n<b>Правильний переклад:</b>\n{html.code(correct_translation)}"
    message += f"\n\n<b>Пояснення:</b>\n{html.code(translation_check_result.explanation)}"
    return message
