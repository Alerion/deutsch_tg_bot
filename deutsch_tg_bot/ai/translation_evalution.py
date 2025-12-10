import time
from dataclasses import dataclass
from functools import cache

import anthropic
from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.ai.anthropic_utils import (
    MessageDict,
    extract_tag_content,
    load_prompt_template_from_file,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.user_session import Sentence

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-names
ANTHROPIC_MODEL = "claude-haiku-4-5"


@dataclass
class TranslationCheckResult:
    messages: list[MessageDict]
    correct_translation: str | None = None
    explanation: str | None = None


async def check_translation(
    sentence: Sentence,
    user_translation: str,
) -> TranslationCheckResult:
    prompt_params = {
        "ukrainian_sentence": sentence.ukrainian_sentence,
        "level": sentence.level.value,
        "tense": sentence.tense.value,
        "user_translation": user_translation,
    }
    evaluate_prompt = get_translation_evaluation_prompt_template() % prompt_params

    messages = [{"role": "user", "content": evaluate_prompt}]
    if settings.MOCK_AI:
        return TranslationCheckResult(
            messages=[*messages, {"role": "assistant", "content": "Все вірно."}],
        )

    start_time = time.time()
    message = await anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4000,
        temperature=0.7,
        messages=[
            *messages,
            {"role": "assistant", "content": "<analysis>"},
        ],
    )

    group_panels = [
        Panel(
            Markdown(
                f"- Model: {ANTHROPIC_MODEL}\n"
                f"- Time taken: {time.time() - start_time:.2f} seconds\n"
            )
        ),
        Panel(Pretty(prompt_params, expand_all=True), title="Prompt Parameters"),
    ]
    if settings.SHOW_TOCKENS_USAGE:
        group_panels.append(Panel(Pretty(message.usage, expand_all=True), title="AI Usage"))

    completion = message.content[0].text.strip()

    if settings.SHOW_FULL_AI_RESPONSE:
        group_panels.append(
            Panel(
                Markdown(completion),
                title="Full AI Response",
            )
        )

    rprint(Panel(Group(*group_panels), title="Translation Evaluation", border_style="blue"))

    messages.append({"role": "assistant", "content": completion})

    correct_translation = extract_tag_content(completion, "correct_translation")
    explanation = extract_tag_content(completion, "explanation")
    return TranslationCheckResult(
        messages=messages,
        correct_translation=correct_translation,
        explanation=explanation,
    )


@cache
def get_translation_evaluation_prompt_template() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("translation_evaluation.txt"))
