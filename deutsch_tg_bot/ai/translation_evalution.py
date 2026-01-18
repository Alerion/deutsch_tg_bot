import time
from functools import cache

from google import genai
from pydantic import BaseModel, Field
from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.ai.prompt_utils import (
    load_prompt_template_from_file,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.data_types import Sentence

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

GOOGLE_MODEL = "gemini-2.5-flash"


class TranslationEvaluationResult(BaseModel):
    planning: str = Field(description="Detailed evaluation of the user's translation.")
    is_translation_correct: bool = Field(
        description="Indicates whether the user's translation is correct."
    )
    correct_translation: str = Field(
        description="The correct German translation of the Ukrainian sentence."
    )
    explanation: str = Field(
        description="Explanation of any mistakes made in the user's translation."
    )


async def evaluate_translation_with_ai(
    sentence: Sentence,
    user_translation: str,
) -> TranslationEvaluationResult:
    prompt_params = {
        "ukrainian_sentence": sentence.ukrainian_sentence,
        "level": sentence.level.value,
        "tense": sentence.tense.value,
        "user_translation": user_translation,
    }
    evaluate_prompt = get_translation_evaluation_prompt_template() % prompt_params

    start_time = time.time()
    response = await genai_client.models.generate_content(
        model=GOOGLE_MODEL,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=TranslationEvaluationResult.model_json_schema(),
        ),
        contents=evaluate_prompt,
    )

    usage = response.usage_metadata
    evaluate_translate_response = TranslationEvaluationResult.model_validate_json(
        response.text or ""
    )

    group_panels = [
        Panel(
            Markdown(
                f"- Model: {GOOGLE_MODEL}\n- Time taken: {time.time() - start_time:.2f} seconds\n"
            )
        ),
        Panel(Pretty(prompt_params, expand_all=True), title="Prompt Parameters"),
    ]
    if settings.SHOW_TOCKENS_USAGE:
        group_panels.append(Panel(Pretty(usage, expand_all=True), title="AI Usage"))

    if settings.SHOW_FULL_AI_RESPONSE:
        group_panels.append(
            Panel(
                Pretty(evaluate_translate_response, expand_all=True),
                title="Full AI Response",
            )
        )

    rprint(Panel(Group(*group_panels), title="Translation Evaluation", border_style="blue"))
    return evaluate_translate_response


@cache
def get_translation_evaluation_prompt_template() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("translation_evaluation.txt"))
