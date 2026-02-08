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
from rich import print as rprint

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.data_types import Sentence
from deutsch_tg_bot.deutsh_enums import DEUTCH_LEVEL_TENSES, DeutschLevel, SentenceTypeProbabilities
from deutsch_tg_bot.situation_training.ai.grammar_checker import check_grammar_with_ai
from deutsch_tg_bot.situation_training.ai.narrator_agent import (
    generate_initial_scene_state,
    generate_narrator_event,
    should_trigger_narrator,
)
from deutsch_tg_bot.situation_training.ai.situation_agent import (
    generate_character_response,
    generate_situation_intro,
)
from deutsch_tg_bot.situation_training.ai.situation_generator import (
    generate_situation_from_description,
)
from deutsch_tg_bot.situation_training.situations import Situation
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
from deutsch_tg_bot.user_session import SentenceTranslationState, SituationTrainingState
from deutsch_tg_bot.utils.random_selector import BalancedRandomSelector


class SituationTraining(StatesGroup):
    describe_situation = State()
    process_user_message = State()


router = Router()


@router.callback_query(F.data == "select_training_type:situation")
async def select_training_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    await callback_query.message.edit_text("Ти обрав тренування 'Рольова гра (ситуації)'")
    await callback_query.message.answer(
        "Опиши ситуацію, в якій ти хочеш потренуватися (наприклад, 'Уяви, що ти в кафе і хочеш замовити каву')",
    )
    await state.set_state(SituationTraining.describe_situation)


@router.message(SituationTraining.describe_situation)
async def describe_situation(message: Message, state: FSMContext) -> None:
    deutsch_level: DeutschLevel = await state.get_value("deutsch_level")

    async with progress(message, "Створюю ситуацію"):
        situation: Situation = await generate_situation_from_description(
            message.text, deutsch_level
        )

        # Generate initial scene state and situation intro in parallel
        scene_state_task = asyncio.create_task(
            generate_initial_scene_state(situation, deutsch_level)
        )
        intro_task = asyncio.create_task(generate_situation_intro(situation, deutsch_level))
        scene_state, (intro_message, chat) = await asyncio.gather(scene_state_task, intro_task)

    situation_training = SituationTrainingState(
        current_situation=situation,
        scene_state=scene_state,
        situation_chat=chat,
    )
    await message.answer(intro_message)
    await state.set_state(SituationTraining.process_user_message)
    await state.update_data(situation_training=situation_training)


@router.message(SituationTraining.process_user_message)
async def process_user_message(message: Message, state: FSMContext) -> None:
    """Handle user's message in roleplay and respond + check grammar."""
    deutsch_level: DeutschLevel = await state.get_value("deutsch_level")
    situation_training = await state.get_value("situation_training")
    assert situation_training is not None

    situation_training.situation_message_count += 1

    # Track dialogue for narrator
    situation_training.recent_dialogue.append(("User", message.text))

    # Check if narrator should trigger
    narrator_context: str | None = None
    trigger_narrator = should_trigger_narrator(
        situation_training.situation_message_count,
        situation_training.last_narrator_event_index,
    )

    # Run grammar check in parallel with other operations
    grammar_task = asyncio.create_task(
        check_grammar_with_ai(
            message.text,
            deutsch_level,
            f"{situation_training.current_situation.name_de} - {situation_training.current_situation.character_role}",
        )
    )

    async with progress(message, "Обробляю відповідь"):
        # If narrator triggers, generate event first
        if trigger_narrator:
            narrator_event = await generate_narrator_event(
                situation_training.current_situation,
                deutsch_level,
                situation_training.scene_state,
                situation_training.recent_dialogue[-6:],  # Last 6 messages
            )

            # Update state
            situation_training.scene_state = narrator_event.updated_state
            situation_training.last_narrator_event_index = (
                situation_training.situation_message_count
            )
            situation_training.recent_dialogue = []  # Reset dialogue tracking
            narrator_context = narrator_event.event_context_for_npc

            # Send narrator event to user if there's a description
            if narrator_event.event_description_de.strip():
                narrator_msg = f"📖 <i>{narrator_event.event_description_de}</i>"
                if narrator_event.event_description_uk.strip():
                    narrator_msg += f"\n<code>({narrator_event.event_description_uk})</code>"
                await message.answer(narrator_msg)

        # Generate character response with narrator context if available
        character_response, updated_chat = await generate_character_response(
            message.text,
            situation_training.situation_chat,
            situation_training.current_situation,
            deutsch_level,
            scene_state=situation_training.scene_state,
            narrator_context=narrator_context,
        )

        grammar_result = await grammar_task

    situation_training.situation_chat = updated_chat

    # Track NPC response in dialogue
    situation_training.recent_dialogue.append(
        (situation_training.current_situation.character_role, character_response.german_response)
    )

    # Send grammar feedback first (as reply to user's message) if there are errors
    if grammar_result.has_errors and grammar_result.brief_feedback:
        feedback_message = f"💡 {grammar_result.brief_feedback}"
        if grammar_result.corrected_text:
            feedback_message += f"\n✓ <i>{grammar_result.corrected_text}</i>"
        await message.answer(feedback_message)

    # Send character's response
    character_msg = (
        f"<b>{situation_training.current_situation.character_role}:</b>\n"
        f"{character_response.german_response}"
    )

    if character_response.is_conversation_complete:
        character_msg += (
            "\n\n<i>--- Розмова завершена ---</i>\n\n"
            f"Ви обмінялися <b>{situation_training.situation_message_count}</b> повідомленнями.\n\n"
            "Введіть /situation щоб обрати нову ситуацію, або /next для перекладу речень."
        )
        await message.answer(character_msg)
        await state.update_data(situation_training=None)
        return

    await message.answer(character_msg)
    await state.update_data(situation_training=situation_training)
