"""AI agent for generating character responses in roleplay situations."""

import os
from functools import cache

from google import genai
from google.genai import chats
from pydantic import BaseModel, Field
from rich import print as rprint
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.situation_training.situations import Situation
from deutsch_tg_bot.utils.prompt_utils import (
    load_prompt_template_from_file,
    replace_promt_placeholder,
)

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

GOOGLE_MODEL = "gemini-2.5-flash"

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class CharacterResponse(BaseModel):
    """Response from the roleplay character."""

    german_response: str = Field(
        description="The character's response in German, appropriate for the situation and user's level."
    )
    is_conversation_complete: bool = Field(
        description="True if the conversation has naturally ended (e.g., goodbye said, transaction complete).",
        default=False,
    )


def _build_system_prompt(situation: Situation, level: DeutschLevel) -> str:
    """Build the system prompt for the character."""
    prompt_template = get_character_system_prompt_template()
    prompt_params = {
        "character_role": situation.character_role,
        "situation_name": situation.name_de,
        "scenario_prompt": situation.scenario_prompt,
        "level": level.value,
    }
    return prompt_template % prompt_params


@cache
def get_character_system_prompt_template() -> str:
    return replace_promt_placeholder(
        load_prompt_template_from_file(PROMPTS_DIR, "character_system_prompt.txt")
    )


async def generate_situation_intro(
    situation: Situation,
    level: DeutschLevel,
) -> tuple[str, chats.AsyncChat]:
    system_prompt = _build_system_prompt(situation, level)

    # Create a chat session with the system prompt as context
    chat = genai_client.chats.create(
        model=GOOGLE_MODEL,
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_json_schema=CharacterResponse.model_json_schema(),
            temperature=0.7,
        ),
    )

    # The opening message is predefined, no need to generate
    intro_message = (
        f"<b>Ситуація:</b> {situation.name_uk}\n"
        f"<b>Ваша роль:</b> {situation.user_role_uk}\n\n"
        f"<b>{situation.character_role}:</b>\n"
        f"<i>{situation.opening_message_de}</i>\n\n"
        f"<code>{situation.opening_message_uk}</code>\n\n"
        "Відповідайте німецькою мовою. Введіть /end щоб завершити ситуацію."
    )

    if settings.SHOW_FULL_AI_RESPONSE:
        rprint(
            Panel(
                Pretty(
                    {
                        "situation": situation.name_de,
                        "level": level.value,
                        "opening_message": situation.opening_message_de,
                    },
                    expand_all=True,
                ),
                title="Situation Started",
                border_style="blue",
            )
        )

    return intro_message, chat


async def generate_character_response(
    user_message: str,
    chat: chats.AsyncChat,
    situation: Situation,
    level: DeutschLevel,
) -> tuple[CharacterResponse, chats.AsyncChat]:
    # Send the user's message and get the character's response
    response = await chat.send_message(
        f"Der Benutzer (auf Niveau {level.value}) sagt: {user_message}"
    )

    response_text = (response.text or "").strip()

    try:
        character_response = CharacterResponse.model_validate_json(response_text)
    except Exception:
        # Fallback if JSON parsing fails
        character_response = CharacterResponse(
            german_response=response_text.replace('"', "").replace("{", "").replace("}", ""),
            is_conversation_complete=False,
        )

    if settings.SHOW_FULL_AI_RESPONSE:
        rprint(
            Panel(
                Pretty(
                    {
                        "user_message": user_message,
                        "character_response": character_response.german_response,
                        "is_complete": character_response.is_conversation_complete,
                    },
                    expand_all=True,
                ),
                title="Character Response",
                border_style="blue",
            )
        )

    return character_response, chat
