"""AI module for checking grammar in user's German messages during roleplay."""

import os
from functools import cache

from google import genai
from pydantic import BaseModel, Field
from rich import print as rprint
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DeutschLevel
from deutsch_tg_bot.utils.prompt_utils import (
    load_prompt_template_from_file,
    replace_promt_placeholder,
)

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

GOOGLE_MODEL = "gemini-2.5-flash"

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class GrammarCheckResult(BaseModel):
    """Result of grammar checking."""

    has_errors: bool = Field(
        description="True if the message contains grammar or vocabulary errors."
    )
    brief_feedback: str | None = Field(
        description="Brief, friendly feedback about errors. None if no errors.",
        default=None,
    )
    corrected_text: str | None = Field(
        description="The corrected version of the text. None if no errors.",
        default=None,
    )


async def check_grammar_with_ai(
    user_text: str,
    level: DeutschLevel,
    situation_context: str,
) -> GrammarCheckResult:
    prompt_template = get_grammar_check_prompt_template()
    prompt_params = {
        "level": level.value,
        "user_text": user_text,
        "situation_context": situation_context,
    }
    prompt = prompt_template % prompt_params

    response = await genai_client.models.generate_content(
        model=GOOGLE_MODEL,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=GrammarCheckResult.model_json_schema(),
            temperature=0.3,  # Lower temperature for more consistent feedback
        ),
        contents=prompt,
    )

    response_text = (response.text or "").strip()
    result = GrammarCheckResult.model_validate_json(response_text)

    if settings.SHOW_FULL_AI_RESPONSE:
        rprint(
            Panel(
                Pretty(
                    {
                        "user_text": user_text,
                        "level": level.value,
                        "has_errors": result.has_errors,
                        "feedback": result.brief_feedback,
                        "corrected": result.corrected_text,
                    },
                    expand_all=True,
                ),
                title="Grammar Check",
                border_style="yellow",
            )
        )

    return result


@cache
def get_grammar_check_prompt_template() -> str:
    return replace_promt_placeholder(
        load_prompt_template_from_file(PROMPTS_DIR, "grammar_check.txt")
    )
