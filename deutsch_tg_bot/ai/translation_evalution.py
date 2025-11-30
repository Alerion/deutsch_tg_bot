from dataclasses import dataclass
from functools import cache

import anthropic
from rich import print as rprint

from deutsch_tg_bot.ai.anthropic_utils import (
    MessageDict,
    extract_tag_content,
    load_prompt_template_from_file,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.user_session import Sentence

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


@dataclass
class TranslationCheckResult:
    messages: list[MessageDict]
    correct_translation: str | None
    explanation: str | None


async def check_translation(
    ukrainian_sentence: Sentence,
    user_translation: str,
) -> TranslationCheckResult:
    prompt = build_check_translation_prompt(
        ukrainian_sentence=ukrainian_sentence,
        user_translation=user_translation,
    )

    messages = [{"role": "user", "content": prompt}]
    response = await anthropic_client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4000,
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "<analysis>"},
        ],
    )
    rprint("--- AI translation evaluation ---")
    rprint(response.content[0].text)
    completion = response.content[0].text.strip()
    messages.append({"role": "assistant", "content": completion})

    correct_translation = extract_tag_content(completion, "correct_translation")
    explanation = extract_tag_content(completion, "explanation")
    return TranslationCheckResult(
        messages=messages,
        correct_translation=correct_translation,
        explanation=explanation,
    )


def build_check_translation_prompt(
    ukrainian_sentence: Sentence,
    user_translation: str,
) -> str:
    params = {
        "ukrainian_sentence": ukrainian_sentence.sentence,
        "level": ukrainian_sentence.level.value,
        "tense": ukrainian_sentence.tense.value,
        "user_translation": user_translation,
    }
    rprint("--- AI params to check translation ---")
    rprint(params)
    return get_translation_evaluation_prompt_template() % params


@cache
def get_translation_evaluation_prompt_template() -> str:
    rprint("Loading translation evaluation prompt template from file...")
    return replace_promt_placeholder(load_prompt_template_from_file("translation_evaluation.txt"))
