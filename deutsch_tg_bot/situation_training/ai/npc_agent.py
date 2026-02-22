from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel

from deutsch_tg_bot.user_session import SituationTrainingState

from .data_types import NPCResponse, NPCState
from .model_settings import google_model_settings

GOOGLE_MODEL = GoogleModel("gemini-2.5-flash")


@dataclass
class NPCContext:
    situation_training_state: SituationTrainingState
    current_npc_state: NPCState
    other_npc_states: list[NPCState]


npc_agent = Agent(
    model=GOOGLE_MODEL,
    model_settings=google_model_settings,
    output_type=NPCResponse,
    deps_type=NPCContext,
    instructions="""
You are an AI agent acting as a NPC in a text-based roleplay game.
Your task is to react to player's actions in a way that is consistent with your personality,
mood and goals, as well as the current game state.
You receive the current game state, including information about the location,
time of day, active NPCs and their states, and history of game's messages.
Based on this information, you generate a reaction to the player's actions in the specified language.
Your reaction should be in character and can include dialogue, actions, or changes in mood.
If player action provoces you to some reaction or action, you should react to it.
Don't be passive or stick to the same reaction. Be creative and try to make the game more dynamic and interesting.
Analye messages history to understand your and player's interaction.
""",
)


@npc_agent.instructions
def add_game_state(ctx: RunContext[NPCContext]) -> str:
    game_state = ctx.deps.situation_training_state.game_state
    return f"""
Current game state:
Game language: {game_state.game_language_code}. All descriptions and reactions must be in this language.
Situation: {game_state.situation_name}
Situation description: {game_state.situation_description}
Location: {game_state.location_name} - {game_state.location_description}
Time of day: {game_state.time_of_day}
Active NPCs: {", ".join(game_state.active_npcs) if game_state.active_npcs else "none"}
World facts: {", ".join(game_state.world_facts) if game_state.world_facts else "none"}
"""


@npc_agent.instructions
def add_current_npc_state(ctx: RunContext[NPCContext]) -> str:
    npc_state = ctx.deps.current_npc_state
    description = f"npc_id: {npc_state.npc_id}. Use this as npc_id in your response!!!\n"
    description += (
        f"NPC: {npc_state.name}, Personality: {npc_state.personality}, Mood: {npc_state.mood}"
    )

    if npc_state.knows_about_player:
        description += f", Knows about player: {', '.join(npc_state.knows_about_player)}"
    if npc_state.goals:
        description += f", Goals: {', '.join(npc_state.goals)}"
    return description


@npc_agent.instructions
def add_other_npcs_state(ctx: RunContext[NPCContext]) -> str:
    other_npc_states = ctx.deps.other_npc_states
    if not other_npc_states:
        return "No other active NPCs."

    npc_descriptions = []
    for npc in other_npc_states:
        description = f"NPC: {npc.name}, Personality: {npc.personality}, Mood: {npc.mood}"
        npc_descriptions.append(description)

    return "\n".join(npc_descriptions)


@npc_agent.instructions
def add_player_state(ctx: RunContext[NPCContext]) -> str:
    player_state = ctx.deps.situation_training_state.player_state
    return f"""
Player: {player_state.name}
Description: {player_state.description}
"""


@npc_agent.instructions
def add_message_history(ctx: RunContext[NPCContext]) -> str:
    messages_history = ctx.deps.situation_training_state.messages_history[:20]
    if not messages_history:
        return "No messages history yet."

    return "Messages history:\n{messages_history!r}"


async def get_npc_reaction(
    npc_id: str,
    situation_training_state: SituationTrainingState,
    latest_player_action: str,
) -> NPCResponse:
    current_npc_state = next(
        npc for npc in situation_training_state.npc_states if npc.npc_id == npc_id
    )
    assert current_npc_state is not None, (
        f"NPC with id {npc_id} not found in the current game state"
    )
    other_npc_states = [npc for npc in situation_training_state.npc_states if npc.npc_id != npc_id]

    npc_context = NPCContext(
        situation_training_state=situation_training_state,
        current_npc_state=current_npc_state,
        other_npc_states=other_npc_states,
    )
    message = f"""Latest player action: {latest_player_action}
Based on the current game state, your NPC's personality, mood and goals, react to this action in character.
Your reaction can include dialogue (what your NPC says to the player or other NPCs),
actions (what your NPC does in response to the player's action)
and changes in mood (how your NPC's mood changes in response to the player's action).
Be creative and make sure your reaction is consistent with the current game state and your NPC's characteristics.
Remember that the game language is {situation_training_state.game_state.game_language_code},
so your reaction must be in this language.
"""
    npc_response = await npc_agent.run(message, deps=npc_context)
    return npc_response.output
