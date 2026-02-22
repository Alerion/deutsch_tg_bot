from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel

from deutsch_tg_bot.user_session import SituationTrainingState

from .data_types import NarratorResponse
from .model_settings import google_model_settings

GOOGLE_MODEL = GoogleModel("gemini-2.5-flash")

narrator_agent = Agent(
    model=GOOGLE_MODEL,
    model_settings=google_model_settings,
    output_type=NarratorResponse,
    deps_type=SituationTrainingState,
    instructions="""
You are an AI agent acting as a narrator for a text-based roleplay game.
Your task is to describe scenes and generate events based on the current game state and player actions.

Generated events should add some dinamics to the situation,
force player and npcs to react to events and change dynamic in their communication.
So, game becomes more interesting and less static. Otherwise, not experienced player
may just write one message, get some reaction from narrator and npcs, and then don't know what to do next.
But, consider passed messages history. If player and npcs already had some interaction,
you can generate events that are logical consequences of this interaction,
just describing what is going on in the scene.
If you see from this history that communication is stuck and game is boring,
you can generate some unexpected event that will change the situation and give new opportunities
for player and npcs to interact.

You receive the current game state, including information about the location,
time of day, active NPCs and their states, and the player's recent actions.
Based on this information, you generate a description of the scene and events in the specified language.
Be precise and concise in your description. Main interaction should be between player and npcs.

Don't generate reactions of NPCs or message of NPCs in your response.
Just describe the scene and events. NPCs reaction is triggered after each player action,
and after you describe the scene and events, NPCs will react to them based on their personality, mood and goals.
If you include NPCs reactions in your response, player will see duplicated reaction of NPC.
""",
)


@narrator_agent.instructions
def add_game_state(ctx: RunContext[SituationTrainingState]) -> str:
    game_state = ctx.deps.game_state
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


@narrator_agent.instructions
def add_npc_states(ctx: RunContext[SituationTrainingState]) -> str:
    npc_states = ctx.deps.npc_states
    if not npc_states:
        return "No active NPCs."

    npc_descriptions = []
    for npc in npc_states:
        description = f"NPC: {npc.name}, Personality: {npc.personality}, Mood: {npc.mood}"
        if npc.knows_about_player:
            description += f", Knows about player: {', '.join(npc.knows_about_player)}"
        if npc.goals:
            description += f", Goals: {', '.join(npc.goals)}"
        npc_descriptions.append(description)

    return "\n".join(npc_descriptions)


@narrator_agent.instructions
def add_player_state(ctx: RunContext[SituationTrainingState]) -> str:
    player_state = ctx.deps.player_state
    return f"""
Player: {player_state.name}
Description: {player_state.description}
Inventory: {", ".join(player_state.inventory) if player_state.inventory else "empty"}
"""


@narrator_agent.instructions
def add_message_history(ctx: RunContext[SituationTrainingState]) -> str:
    messages_history = ctx.deps.messages_history[:20]
    if not messages_history:
        return "No messages history yet."

    return "Messages history:\n{messages_history!r}"


async def get_narrator_response(
    situation_training_state: SituationTrainingState, latest_player_action: str
) -> NarratorResponse:
    message = f"""Latest player action: {latest_player_action}
Based on the current game state, describe the scene and events, and determine which NPCs should react to this action."""
    response = await narrator_agent.run(message, deps=situation_training_state)
    return response.output
