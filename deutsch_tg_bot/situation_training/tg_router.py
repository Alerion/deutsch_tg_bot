from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    Message,
)

from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.situation_training.ai.data_types import NPCResponse
from deutsch_tg_bot.situation_training.ai.narrator_agent import get_narrator_response
from deutsch_tg_bot.situation_training.ai.npc_agent import get_npc_reaction
from deutsch_tg_bot.situation_training.ai.situation_generator import (
    generate_situation_from_description,
)
from deutsch_tg_bot.tg_progress import progress
from deutsch_tg_bot.user_session import SituationTrainingState


class SituationTraining(StatesGroup):
    describe_situation = State()
    process_user_message = State()


router = Router()


@router.callback_query(F.data == "select_training_type:situation")
async def select_training_type(callback_query: CallbackQuery, state: FSMContext) -> None:
    assert isinstance(callback_query.message, Message)
    await callback_query.message.edit_text("Ти обрав тренування 'Рольова гра (ситуації)'")
    await callback_query.message.answer(
        "Опиши ситуацію, в якій ти хочеш потренуватися (наприклад, 'Уяви, що ти в кафе і хочеш замовити каву')",
    )
    await state.set_state(SituationTraining.describe_situation)


@router.message(SituationTraining.describe_situation)
async def describe_situation(message: Message, state: FSMContext) -> None:
    async with progress(message, "Створюю ситуацію"):
        assert message.text is not None
        if message.text.strip() == "1":
            description = """
Я Нео на самому початку фільму Матриця.
Я ще нічого не знаю про Матрицю, живу звичайним життям в місті, працюю програмістом.
Я відчуваю, що щось не так з світом, але не можу зрозуміти що саме.
Я відчуваю себе в пастці, як ніби я не на своєму місці.
Я часто відчуваю тривогу і розгубленість через це.
Я не знаю, що таке Матриця і що вона означає для мене.
Пізній вечір, я в своїй квартирі, сиджу за комп'ютером і працюю над кодом.
Тут в двері дзвонять. За дверима стоїть Морфеус.
"""
        else:
            description = message.text

        game_state, npc_states, player_state = await generate_situation_from_description(
            user_description=description,
            game_language_code="uk",
        )

    situation_training_state = SituationTrainingState(
        game_state=game_state,
        npc_states=npc_states,
        player_state=player_state,
    )

    # First reasction of narrator based on initial situation description
    latest_player_action = """
Гравець входить в ситуацію. Ще не зробив жодної дії.
Обовʼязково потрібна якась реакція чи дія, щоб тригернути динаміку в ситуації.
Інакше, гравець може просто не знати, що робити далі.
"""
    async with progress(message, "Наратор думає..."):
        narrator_response = await get_narrator_response(
            situation_training_state=situation_training_state,
            latest_player_action=latest_player_action,
        )

    situation_training_state.messages_history.append(
        {"sender": "narrator", "text": narrator_response.narrator_action}
    )
    narrator_msg = f"📖 <i>{narrator_response.narrator_action}</i>"
    await message.answer(narrator_msg)

    for npc_id in game_state.active_npcs:
        async with progress(message, f"{npc_id} думає..."):
            npc_response = await get_npc_reaction(
                npc_id=npc_id,
                situation_training_state=situation_training_state,
                latest_player_action=latest_player_action,
            )
        apply_npc_response_to_state(situation_training_state, npc_response)
        situation_training_state.messages_history.append(
            {"sender": npc_id, "text": npc_response.action_or_speech}
        )
        npc_msg = f"<b>{npc_response.npc_id}:</b>\n{npc_response.action_or_speech}"
        await message.answer(npc_msg)

    await state.set_state(SituationTraining.process_user_message)
    await state.update_data(situation_training_state=situation_training_state)


@router.message(SituationTraining.process_user_message)
async def process_user_message(message: Message, state: FSMContext) -> None:
    """Handle user's message in roleplay and respond + check grammar."""
    deutsch_level = await state.get_value("deutsch_level")
    assert isinstance(deutsch_level, DeutschLevel)
    situation_training_state = await state.get_value("situation_training_state")
    assert isinstance(situation_training_state, SituationTrainingState)

    situation_training_state.player_message_count += 1

    assert message.text is not None
    latest_player_action = message.text

    # FIXME: Sometime user message should trigger narrator response.
    #        For example, if user makes some action and is exepcting some reaction from the world.
    if should_trigger_narrator(situation_training_state):
        async with progress(message, "Наратор думає..."):
            narrator_response = await get_narrator_response(
                situation_training_state=situation_training_state,
                latest_player_action=latest_player_action,
            )

        situation_training_state.messages_history.append(
            {"sender": "narrator", "text": narrator_response.narrator_action}
        )
        narrator_msg = f"📖 <i>{narrator_response.narrator_action}</i>"
        await message.answer(narrator_msg)

    for npc_id in situation_training_state.game_state.active_npcs:
        async with progress(message, f"{npc_id} думає..."):
            npc_response = await get_npc_reaction(
                npc_id=npc_id,
                situation_training_state=situation_training_state,
                latest_player_action=latest_player_action,
            )
        apply_npc_response_to_state(situation_training_state, npc_response)
        situation_training_state.messages_history.append(
            {"sender": npc_id, "text": npc_response.action_or_speech}
        )
        npc_msg = f"<b>{npc_response.npc_id}:</b>\n{npc_response.action_or_speech}"
        await message.answer(npc_msg)

    situation_training_state.messages_history.append(
        {"sender": "player", "text": latest_player_action}
    )

    await state.update_data(situation_training_state=situation_training_state)


def should_trigger_narrator(
    situation_training_state: SituationTrainingState,
    trigger_after_player_messages: int = 3,
) -> bool:
    trigger_narrator = (
        situation_training_state.player_message_count
        - situation_training_state.last_narrator_event_index
    ) >= trigger_after_player_messages
    if trigger_narrator:
        situation_training_state.last_narrator_event_index = (
            situation_training_state.player_message_count
        )
    return trigger_narrator


def apply_npc_response_to_state(
    situation_training_state: SituationTrainingState, npc_response: NPCResponse
) -> None:
    npc = next(
        (npc for npc in situation_training_state.npc_states if npc.npc_id == npc_response.npc_id),
        None,
    )
    assert npc is not None, f"NPC with id {npc_response.npc_id} not found in the current game state"

    if npc_response.mood_update:
        npc.mood = npc_response.mood_update
    if npc_response.learns_about_player:
        npc.knows_about_player.extend(npc_response.learns_about_player)
