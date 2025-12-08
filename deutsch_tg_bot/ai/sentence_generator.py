import random
import time
from functools import cache
from itertools import cycle
from typing import Any

import anthropic
from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.ai.anthropic_utils import (
    extract_tag_content,
    load_prompt_template_from_file,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import (
    DEUTCH_LEVEL_TENSES,
    DeutschLevel,
    DeutschTense,
    SentenceType,
    SentenceTypeProbabilities,
)
from deutsch_tg_bot.user_session import Sentence

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-names
ANTHROPIC_MODEL = "claude-haiku-4-5"

_times = []


async def generate_sentence(
    level: DeutschLevel, previous_sentences: list[Sentence], optional_constraint: str | None
) -> Sentence:
    tense = get_random_tense_for_level(level)
    sentence_type = get_random_sentence_type()

    if settings.MOCK_AI:
        rprint("[yellow]Using MOCK_AI mode - returning mocked sentence[/yellow]")
        return get_mocked_sentence(level, tense)

    system_prompt = get_sentence_generator_system_prompt()
    user_prompt, prompt_params = build_dynamic_user_prompt(
        level=level,
        tense=tense,
        sentence_type=sentence_type,
        previous_sentences=previous_sentences,
        optional_constraint=optional_constraint,
    )

    start_time = time.time()
    message = await anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
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

    _times.append(time.time() - start_time)
    average_time = sum(_times) / len(_times)
    panel_group = Group(
        Panel(
            Markdown(
                f"- Model: {ANTHROPIC_MODEL}\n"
                f"- Time taken: {_times[0]:.2f} seconds\n"
                f"- Average time: {average_time:.2f} seconds\n",
            )
        ),
        Panel(Pretty(prompt_params, expand_all=True), title="Prompt Parameters"),
        Panel(Pretty(message.usage, expand_all=True), title="AI Usage"),
    )
    rprint(Panel(panel_group, title="Sentence Generation", border_style="green"))

    completion = message.content[0].text.strip()
    # rprint(
    #     Panel(
    #         Markdown(completion),
    #         title="Generated Sentence",
    #         subtitle="full response",
    #         border_style="green"
    #     )
    # )

    ukrainian_sentence = extract_tag_content(completion, "ukrainian_sentence")
    german_sentence = extract_tag_content(completion, "german_sentence")
    return Sentence(
        sentence_type=sentence_type,
        ukrainian_sentence=ukrainian_sentence,
        german_sentence=german_sentence,
        tense=tense,
        level=level,
    )


def get_random_tense_for_level(level: DeutschLevel) -> DeutschTense:
    tenses = DEUTCH_LEVEL_TENSES[level]
    return random.choice(tenses)


def get_random_sentence_type() -> SentenceType:
    sentence_types = list(SentenceTypeProbabilities.keys())
    probabilities = list(SentenceTypeProbabilities.values())
    return random.choices(sentence_types, weights=probabilities, k=1)[0]


def build_dynamic_user_prompt(
    level: DeutschLevel,
    tense: DeutschTense,
    sentence_type: SentenceType,
    previous_sentences: list[Sentence],
    optional_constraint: str | None,
) -> tuple[str, dict[str, Any]]:
    previous_sentences = [s.ukrainian_sentence for s in previous_sentences]
    params = {
        "level": level.value,
        "tense": tense.value,
        "sentence_type": sentence_type.value,
        "previous_sentences": "\n".join(previous_sentences),
        "optional_constraint": optional_constraint or "",
    }
    prompt = get_sentence_generator_message_template() % params
    return prompt, params


@cache
def get_sentence_generator_message_template() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("generate_sentence_user.txt"))


@cache
def get_sentence_generator_system_prompt() -> str:
    return load_prompt_template_from_file("generate_sentence_system.txt")


async def get_system_prompt_token_count() -> dict[str, Any]:
    system_prompt = get_sentence_generator_system_prompt()
    response = await anthropic_client.messages.count_tokens(
        model=ANTHROPIC_MODEL,
        system=system_prompt,
        messages=[{"role": "user", "content": "Hello"}],
    )
    return response.model_dump_json()


def get_mocked_sentence(level: DeutschLevel, tense: DeutschTense) -> Sentence:
    ukrainian_sentence = next(mocked_ukrainian_sentences)
    return Sentence(
        ukrainian_sentence=ukrainian_sentence,
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
