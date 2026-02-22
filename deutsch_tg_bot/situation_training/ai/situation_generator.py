"""AI module for generating custom situations from user descriptions."""

import os
from uuid import uuid4

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from .data_types import GameState, NPCState, PlayerState

GOOGLE_MODEL = "gemini-2.5-flash"
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class GameStateGenerationResponse(BaseModel):
    game_state: GameState = Field(
        description="Generated initial game state based on the user's situation description"
    )
    npc_states: list[NPCState] = Field(
        default_factory=list,
        description="List of NPC states for each active NPC in the scene based on the generated game state",
    )
    player_state: PlayerState = Field(
        description="Initial state of the player character based on the generated game state"
    )


agent = Agent(
    model=GOOGLE_MODEL,
    output_type=GameStateGenerationResponse,
    instructions="""
Це підготовка до текстової рольової гри для практики німецької мови.
Твоя задача - створити початкову ситуацію на основі опису користувача.
Для `session_id` використовуй передане значення.
""",
)


async def generate_situation_from_description(
    user_description: str,
    game_language_code: str,
) -> tuple[GameState, list[NPCState], PlayerState]:
    message = f"""
Опис ситуації: {user_description!r}
session_id: {str(uuid4())}
Мова гри: {game_language_code}

Згенеруй початковий стан гри на основі цього опису.
"""
    response = await agent.run(message)
    output = response.output
    return (output.game_state, output.npc_states, output.player_state)
