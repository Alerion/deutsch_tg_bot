"""ConversationHandler for situation simulation training."""

import asyncio
from typing import cast

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
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
from deutsch_tg_bot.situation_training.situations import (
    SITUATIONS,
    Situation,
    get_situations_for_level,
)
from deutsch_tg_bot.tg_progress import progress
from deutsch_tg_bot.user_session import UserSession

# States for situation training
SELECT_SITUATION = 10
ROLEPLAY_CONVERSATION = 11
END = ConversationHandler.END


async def start_situation_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show available situations for the user's level."""
    if update.message is None:
        raise ValueError("Expected a message in update")
    if context.user_data is None:
        raise ValueError("Expected user_data in context")

    user_session = cast(UserSession, context.user_data["session"])
    if user_session.level is None:
        raise ValueError("Expected level in user_session")

    available_situations = get_situations_for_level(user_session.level)

    # Build keyboard with situation names
    buttons = []
    row = []
    for i, situation in enumerate(available_situations):
        row.append(situation.name_uk)
        if len(row) == 2 or i == len(available_situations) - 1:
            buttons.append(row)
            row = []

    keyboard = ReplyKeyboardMarkup(
        buttons,
        one_time_keyboard=True,
        input_field_placeholder="Оберіть ситуацію",
    )

    await update.message.reply_text(
        f"Твій рівень: <b>{user_session.level.value}</b>\n\n"
        "Обери ситуацію для рольової гри:\n\n"
        "<i>Ти будеш спілкуватися німецькою з персонажем. "
        "Бот перевірятиме твою граматику та надсилатиме підказки.</i>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    return SELECT_SITUATION


async def handle_situation_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's situation selection and start the roleplay."""
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")
    if context.user_data is None:
        raise ValueError("Expected user_data in context")

    user_session = cast(UserSession, context.user_data["session"])
    if user_session.level is None:
        raise ValueError("Expected level in user_session")

    selected_name = update.message.text.strip()

    # Find the selected situation
    selected_situation: Situation | None = None
    for situation in SITUATIONS.values():
        if situation.name_uk == selected_name:
            selected_situation = situation
            break

    if selected_situation is None:
        # Invalid selection - ask again
        available_situations = get_situations_for_level(user_session.level)
        buttons = []
        row = []
        for i, situation in enumerate(available_situations):
            row.append(situation.name_uk)
            if len(row) == 2 or i == len(available_situations) - 1:
                buttons.append(row)
                row = []

        keyboard = ReplyKeyboardMarkup(
            buttons,
            one_time_keyboard=True,
            input_field_placeholder="Оберіть ситуацію",
        )

        await update.message.reply_text(
            "Будь ласка, обери ситуацію з клавіатури:",
            reply_markup=keyboard,
        )
        return SELECT_SITUATION

    # Initialize the situation
    user_session.current_situation = selected_situation
    user_session.situation_message_count = 0
    user_session.last_narrator_event_index = 0
    user_session.recent_dialogue = []

    async with progress(update, "Готую ситуацію"):
        # Generate initial scene state and situation intro in parallel
        scene_state_task = asyncio.create_task(
            generate_initial_scene_state(selected_situation, user_session.level)
        )
        intro_task = asyncio.create_task(
            generate_situation_intro(selected_situation, user_session.level)
        )

        scene_state, (intro_message, chat) = await asyncio.gather(scene_state_task, intro_task)
        user_session.scene_state = scene_state
        user_session.situation_chat = chat

    await update.message.reply_text(
        intro_message,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    return ROLEPLAY_CONVERSATION


async def handle_roleplay_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user's message in roleplay and respond + check grammar."""
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")
    if context.user_data is None:
        raise ValueError("Expected user_data in context")

    user_session = cast(UserSession, context.user_data["session"])
    if user_session.level is None:
        raise ValueError("Expected level in user_session")
    if user_session.current_situation is None:
        raise ValueError("Expected current_situation in user_session")
    if user_session.situation_chat is None:
        raise ValueError("Expected situation_chat in user_session")

    user_message = update.message.text.strip()
    user_session.situation_message_count += 1

    # Track dialogue for narrator
    user_session.recent_dialogue.append(("User", user_message))

    # Check if narrator should trigger
    narrator_context: str | None = None
    trigger_narrator = should_trigger_narrator(
        user_session.situation_message_count,
        user_session.last_narrator_event_index,
    )

    # Run grammar check in parallel with other operations
    grammar_task = asyncio.create_task(
        check_grammar_with_ai(
            user_message,
            user_session.level,
            f"{user_session.current_situation.name_de} - {user_session.current_situation.character_role}",
        )
    )

    async with progress(update, "Обробляю відповідь"):
        # If narrator triggers, generate event first
        if trigger_narrator and user_session.scene_state:
            narrator_event = await generate_narrator_event(
                user_session.current_situation,
                user_session.level,
                user_session.scene_state,
                user_session.recent_dialogue[-6:],  # Last 6 messages
            )

            # Update state
            user_session.scene_state = narrator_event.updated_state
            user_session.last_narrator_event_index = user_session.situation_message_count
            user_session.recent_dialogue = []  # Reset dialogue tracking
            narrator_context = narrator_event.event_context_for_npc

            # Send narrator event to user if there's a description
            if narrator_event.event_description_de.strip():
                await update.message.reply_text(
                    f"📖 <i>{narrator_event.event_description_de}</i>",
                    parse_mode="HTML",
                )

        # Generate character response with narrator context if available
        character_response, updated_chat = await generate_character_response(
            user_message,
            user_session.situation_chat,
            user_session.current_situation,
            user_session.level,
            scene_state=user_session.scene_state,
            narrator_context=narrator_context,
        )

        grammar_result = await grammar_task

    user_session.situation_chat = updated_chat

    # Track NPC response in dialogue
    user_session.recent_dialogue.append(
        (user_session.current_situation.character_role, character_response.german_response)
    )

    # Send grammar feedback first (as reply to user's message) if there are errors
    if grammar_result.has_errors and grammar_result.brief_feedback:
        feedback_message = f"💡 {grammar_result.brief_feedback}"
        if grammar_result.corrected_text:
            feedback_message += f"\n✓ <i>{grammar_result.corrected_text}</i>"
        await update.message.reply_text(
            feedback_message,
            parse_mode="HTML",
        )

    # Send character's response
    character_msg = (
        f"<b>{user_session.current_situation.character_role}:</b>\n"
        f"{character_response.german_response}"
    )

    if character_response.is_conversation_complete:
        character_msg += (
            "\n\n<i>--- Розмова завершена ---</i>\n\n"
            f"Ви обмінялися <b>{user_session.situation_message_count}</b> повідомленнями.\n\n"
            "Введіть /situation щоб обрати нову ситуацію, або /next для перекладу речень."
        )
        await update.message.reply_text(character_msg, parse_mode="HTML")
        # Reset situation state
        _reset_situation_state(user_session)
        return END

    await update.message.reply_text(character_msg, parse_mode="HTML")
    return ROLEPLAY_CONVERSATION


def _reset_situation_state(user_session: UserSession) -> None:
    """Reset all situation-related state."""
    user_session.current_situation = None
    user_session.situation_chat = None
    user_session.situation_message_count = 0
    user_session.scene_state = None
    user_session.last_narrator_event_index = 0
    user_session.recent_dialogue = []


async def end_situation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /end command to finish current situation."""
    if update.message is None:
        raise ValueError("Expected a message in update")
    if context.user_data is None:
        raise ValueError("Expected user_data in context")

    user_session = cast(UserSession, context.user_data["session"])

    message_count = user_session.situation_message_count

    # Reset situation state
    _reset_situation_state(user_session)

    await update.message.reply_text(
        f"Ситуацію завершено.\n"
        f"Ви обмінялися <b>{message_count}</b> повідомленнями.\n\n"
        "Введіть /situation щоб обрати нову ситуацію, або /next для перекладу речень.",
        parse_mode="HTML",
    )

    return END


# Nested ConversationHandler for situation training
situation_training_handler = ConversationHandler(
    entry_points=[CommandHandler("situation", start_situation_selection)],
    states={
        SELECT_SITUATION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_situation_selection)
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
