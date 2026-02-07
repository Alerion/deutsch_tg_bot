"""ConversationHandler for situation simulation training."""

import asyncio

from telegram import ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from deutsch_tg_bot.command_handlers.stop import stop_command
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
from deutsch_tg_bot.tg_progress import progress
from deutsch_tg_bot.user_session import SituationTrainingState
from deutsch_tg_bot.utils.handler_validation import ValidatedUpdate, check_handler_acces

# States for situation training
SITUATION_DESCRIPTION_INPUT = 10
ROLEPLAY_CONVERSATION = 11
END = ConversationHandler.END


async def start_situation_selection(vu: ValidatedUpdate) -> int:
    """Ask user to describe the situation they want to practice."""

    await vu.message.reply_text(
        f"Твій рівень: <b>{vu.session.deutsch_level.value}</b>\n\n"
        "Опиши ситуацію, яку хочеш потренувати.\n\n"
        "<i>Наприклад:</i>\n"
        "• Розмова з механіком про ремонт машини\n"
        "• Замовлення піци по телефону\n"
        "• Запис до перукаря\n"
        "• Скарга на шумних сусідів\n\n"
        "<i>Ти будеш спілкуватися німецькою з персонажем. "
        "Бот перевірятиме твою граматику та надсилатиме підказки.</i>",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    return SITUATION_DESCRIPTION_INPUT


handle_situation_selection = check_handler_acces(start_situation_selection)


@check_handler_acces
async def handle_situation_description(vu: ValidatedUpdate) -> int:
    """Handle user's custom situation description and start the roleplay."""
    user_description = vu.message_text
    deutsch_level = vu.session.deutsch_level

    async with progress(vu, "Створюю ситуацію"):
        custom_situation = await generate_situation_from_description(
            user_description,
            deutsch_level,
        )

        # Generate initial scene state and situation intro in parallel
        scene_state_task = asyncio.create_task(
            generate_initial_scene_state(custom_situation, deutsch_level)
        )
        intro_task = asyncio.create_task(generate_situation_intro(custom_situation, deutsch_level))

        scene_state, (intro_message, chat) = await asyncio.gather(scene_state_task, intro_task)
        vu.session.situation_training = SituationTrainingState(
            current_situation=custom_situation,
            scene_state=scene_state,
            situation_chat=chat,
        )

    await vu.message.reply_text(
        intro_message,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    return ROLEPLAY_CONVERSATION


@check_handler_acces
async def handle_roleplay_message(vu: ValidatedUpdate) -> int:
    """Handle user's message in roleplay and respond + check grammar."""
    situation_training = vu.session.situation_training
    assert situation_training is not None

    situation_training.situation_message_count += 1

    # Track dialogue for narrator
    situation_training.recent_dialogue.append(("User", vu.message_text))

    # Check if narrator should trigger
    narrator_context: str | None = None
    trigger_narrator = should_trigger_narrator(
        situation_training.situation_message_count,
        situation_training.last_narrator_event_index,
    )

    # Run grammar check in parallel with other operations
    grammar_task = asyncio.create_task(
        check_grammar_with_ai(
            vu.message_text,
            vu.session.deutsch_level,
            f"{situation_training.current_situation.name_de} - {situation_training.current_situation.character_role}",
        )
    )

    async with progress(vu, "Обробляю відповідь"):
        # If narrator triggers, generate event first
        if trigger_narrator:
            narrator_event = await generate_narrator_event(
                situation_training.current_situation,
                vu.session.deutsch_level,
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
                await vu.message.reply_text(narrator_msg, parse_mode="HTML")

        # Generate character response with narrator context if available
        character_response, updated_chat = await generate_character_response(
            vu.message_text,
            situation_training.situation_chat,
            situation_training.current_situation,
            vu.session.deutsch_level,
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
        await vu.message.reply_text(
            feedback_message,
            parse_mode="HTML",
        )

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
        await vu.message.reply_text(character_msg, parse_mode="HTML")
        vu.session.situation_training = None
        return END

    await vu.message.reply_text(character_msg, parse_mode="HTML")
    return ROLEPLAY_CONVERSATION


@check_handler_acces
async def end_situation(vu: ValidatedUpdate) -> int:
    """Handle /end command to finish current situation."""
    vu.session.situation_training = None

    await vu.message.reply_text(
        "Ситуацію завершено.\n"
        "Введіть /situation щоб обрати нову ситуацію, або /next для перекладу речень.",
        parse_mode="HTML",
    )

    return END


# Nested ConversationHandler for situation training
situation_training_handler = ConversationHandler(
    entry_points=[
        CommandHandler("situation", handle_situation_selection),
        # Allow direct entry via text (for situation description input)
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_situation_description),
    ],
    states={
        SITUATION_DESCRIPTION_INPUT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_situation_description)
        ],
        ROLEPLAY_CONVERSATION: [
            CommandHandler("end", end_situation),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_roleplay_message),
        ],
    },
    fallbacks=[
        CommandHandler("end", end_situation),
        CommandHandler("stop", stop_command),
    ],
    map_to_parent={END: END},
    allow_reentry=True,
)
