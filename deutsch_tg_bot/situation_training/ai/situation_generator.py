"""AI module for generating custom situations from user descriptions."""

import os

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.utils.prompt_utils import (
    load_prompt_template_from_file,
)

GOOGLE_MODEL = "gemini-2.5-flash"
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class Situation(BaseModel):
    """AI-generated situation from user description."""

    name_uk: str = Field(description="Short Ukrainian name for the situation (2-4 words)")
    name_de: str = Field(description="German name for the situation")
    character_role: str = Field(description="The NPC's role in German (e.g., Verkäufer, Arzt)")
    user_role_uk: str = Field(description="Description of user's role in Ukrainian (1 sentence)")
    user_role_de: str = Field(description="Description of user's role in German (1 sentence)")
    scenario_prompt: str = Field(
        description="Detailed scenario prompt in German for the AI character (5-10 sentences)"
    )
    opening_message_de: str = Field(
        description="Character's opening message in German (1-2 sentences)"
    )
    opening_message_uk: str = Field(
        description="Ukrainian explanation of the opening message in parentheses"
    )


class UserContext(BaseModel):
    user_description: str = Field(description="User's description of the desired situation")
    deutsch_level: DeutschLevel = Field(description="User's German proficiency level")


agent = Agent(
    model=GOOGLE_MODEL,
    output_type=Situation,
    deps_type=UserContext,
    instructions=load_prompt_template_from_file(PROMPTS_DIR, "generate_situation.txt"),
)


@agent.instructions
async def add_context(ctx: RunContext[UserContext]) -> str:
    return f"""
    Beschreibung des Benutzers (auf Ukrainisch):
    {ctx.deps.user_description!r}

    Sprachniveau des Benutzers: {ctx.deps.deutsch_level}
    """


async def generate_situation_from_description(
    user_description: str,
    level: DeutschLevel,
) -> Situation:
    deps = UserContext(
        user_description=user_description,
        deutsch_level=level,
    )
    response = await agent.run("Situation erzeugen", deps=deps)
    return response.output
