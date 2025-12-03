import random
from functools import cache
from itertools import cycle
from typing import Any

import anthropic
from rich import print as rprint

from deutsch_tg_bot.ai.anthropic_utils import (
    extract_tag_content,
    load_prompt_template_from_file,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DEUTCH_LEVEL_TENSES, DeutschLevel, DeutschTense
from deutsch_tg_bot.user_session import Sentence

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


async def generate_sentence(
    level: DeutschLevel, previous_sentences: list[Sentence], optional_constraint: str | None
) -> Sentence:
    tense = get_random_tense_for_level(level)

    if settings.MOCK_AI:
        rprint("[yellow]Using MOCK_AI mode - returning mocked sentence[/yellow]")
        return get_mocked_sentence(level, tense)

    system_prompt = get_sentence_generator_system_prompt()
    user_prompt = build_dynamic_user_prompt(
        level=level,
        tense=tense,
        previous_sentences=previous_sentences,
        optional_constraint=optional_constraint,
    )

    message = await anthropic_client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=3000,
        temperature=1.0,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},  # This enables caching
            }
        ],
        messages=[
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "<sentence_planning>"},
        ],
    )

    rprint("--- AI generated sentence ---")
    rprint(message.content[0].text)
    rprint("-------- Usage --------")
    rprint(message.usage)

    completion = message.content[0].text.strip()
    ukrainian_sentence = extract_tag_content(completion, "ukrainian_sentence")
    return Sentence(
        sentence=ukrainian_sentence,
        tense=tense,
        level=level,
    )


def get_random_tense_for_level(level: DeutschLevel) -> DeutschTense:
    tenses = DEUTCH_LEVEL_TENSES[level]
    return random.choice(tenses)


def build_dynamic_user_prompt(
    level: DeutschLevel,
    tense: DeutschTense,
    previous_sentences: list[Sentence],
    optional_constraint: str | None,
) -> str:
    previous_sentences = [s.sentence for s in previous_sentences]
    params = {
        "previous_sentences": "\n".join(previous_sentences),
        "level": level.value,
        "tense": tense.value,
        "optional_constraint": optional_constraint or "",
    }
    rprint("--- AI params to generate sentence ---")
    rprint(params)
    return get_sentence_generator_message_template() % params


@cache
def get_sentence_generator_message_template() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("generate_sentence_user.txt"))


@cache
def get_sentence_generator_system_prompt() -> str:
    return load_prompt_template_from_file("generate_sentence_system.txt")


async def get_system_prompt_token_count() -> dict[str, Any]:
    system_prompt = get_sentence_generator_system_prompt()
    response = await anthropic_client.messages.count_tokens(
        model=settings.ANTHROPIC_MODEL,
        system=system_prompt,
        messages=[{"role": "user", "content": "Hello"}],
    )
    return response.model_dump_json()


def get_mocked_sentence(level: DeutschLevel, tense: DeutschTense) -> Sentence:
    ukrainian_sentence = next(mocked_ukrainian_sentences)
    return Sentence(
        sentence=ukrainian_sentence,
        tense=tense,
        level=level,
    )


mocked_ukrainian_sentences = cycle(
    [
        "Це моя книга.",
        "Вона йде до школи.",
        "Ми граємо у футбол.",
        "Вони живуть у великому місті.",
        "Я люблю читати книги.",
    ]
)
