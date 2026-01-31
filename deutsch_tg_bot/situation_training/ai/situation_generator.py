"""AI module for generating custom situations from user descriptions."""

import os
from functools import cache

from google import genai
from pydantic import BaseModel, Field
from rich import print as rprint
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.situation_training.situations import Situation, SituationType
from deutsch_tg_bot.utils.prompt_utils import (
    load_prompt_template_from_file,
    replace_promt_placeholder,
)

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

GOOGLE_MODEL = "gemini-2.5-flash"

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class GeneratedSituation(BaseModel):
    """AI-generated situation from user description."""

    name_uk: str = Field(description="Short Ukrainian name for the situation (2-4 words)")
    name_de: str = Field(description="German name for the situation")
    character_role: str = Field(description="The NPC's role in German (e.g., Verkäufer, Arzt)")
    user_role_uk: str = Field(description="Description of user's role in Ukrainian (1 sentence)")
    scenario_prompt: str = Field(
        description="Detailed scenario prompt in German for the AI character (5-10 sentences)"
    )
    opening_message_de: str = Field(
        description="Character's opening message in German (1-2 sentences)"
    )
    opening_message_uk: str = Field(
        description="Ukrainian explanation of the opening message in parentheses"
    )


@cache
def get_situation_generator_prompt_template() -> str:
    return replace_promt_placeholder(
        load_prompt_template_from_file(PROMPTS_DIR, "generate_situation.txt")
    )


async def generate_situation_from_description(
    user_description: str,
    level: DeutschLevel,
) -> Situation:
    prompt_template = get_situation_generator_prompt_template()
    prompt = prompt_template % {
        "user_description": user_description,
        "level": level.value,
    }

    response = await genai_client.models.generate_content(
        model=GOOGLE_MODEL,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=GeneratedSituation.model_json_schema(),
            temperature=0.7,
        ),
        contents=prompt,
    )

    response_text = (response.text or "").strip()

    try:
        generated = GeneratedSituation.model_validate_json(response_text)
    except Exception as e:
        if settings.SHOW_FULL_AI_RESPONSE:
            rprint(f"[red]Situation generation failed: {e}[/red]")
            rprint(f"[red]Response: {response_text}[/red]")
        # Fallback to a generic situation
        generated = GeneratedSituation(
            name_uk="Власна ситуація",
            name_de="Eigene Situation",
            character_role="Gesprächspartner",
            user_role_uk="Ви учасник розмови",
            scenario_prompt=f"""Du bist ein freundlicher Gesprächspartner in einer alltäglichen Situation.
Der Benutzer möchte folgendes üben: {user_description}
Sprich auf Niveau {level.value}. Sei hilfsbereit und führe ein natürliches Gespräch.""",
            opening_message_de="Guten Tag! Wie kann ich Ihnen helfen?",
            opening_message_uk="(Співрозмовник вітає вас)",
        )

    situation = Situation(
        type=SituationType.BAKERY,  # Using BAKERY as placeholder for custom
        name_uk=generated.name_uk,
        name_de=generated.name_de,
        character_role=generated.character_role,
        user_role_uk=generated.user_role_uk,
        min_level=level,
        scenario_prompt=generated.scenario_prompt,
        opening_message_de=generated.opening_message_de,
        opening_message_uk=generated.opening_message_uk,
    )

    if settings.SHOW_FULL_AI_RESPONSE:
        rprint(
            Panel(
                Pretty(
                    {
                        "user_description": user_description,
                        "level": level.value,
                        "generated": generated.model_dump(),
                    },
                    expand_all=True,
                ),
                title="Generated Situation",
                border_style="green",
            )
        )

    return situation
