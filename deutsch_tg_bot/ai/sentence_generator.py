import random
from functools import cache

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
    prompt = build_sentence_generator_prompt(
        level=level,
        tense=tense,
        previous_sentences=previous_sentences,
        optional_constraint=optional_constraint,
    )
    message = await anthropic_client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=3000,
        temperature=1.0,
        messages=[
            {"role": "user", "content": prompt},
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


def build_sentence_generator_prompt(
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
    return get_sentence_generator_prompt_template() % params


@cache
def get_sentence_generator_prompt_template() -> str:
    rprint("Loading sentence generator prompt template from file...")
    return replace_promt_placeholder(load_prompt_template_from_file("generate_sentence.txt"))
