import random
import re
import time
from functools import cache
from itertools import cycle
from typing import Any, TypedDict

import anthropic
from httpx import get
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

# https://platform.claude.com/docs/en/api/messages#model
ANTHROPIC_MODEL = "claude-haiku-4-5"

_times = []


class SentenceGeneratorParams(TypedDict):
    level: DeutschLevel
    tense: DeutschTense
    sentence_type: SentenceType
    optional_constraint: str | None
    sentence_theme: str | None
    sentence_theme_topic: str | None


def get_sentence_generator_params(
    level: DeutschLevel, optional_constraint: str | None
) -> SentenceGeneratorParams:
    user_prompt_params: SentenceGeneratorParams = {
        "level": level,
        "tense": get_random_tense_for_level(level),
        "sentence_type": get_random_sentence_type(),
        "optional_constraint": optional_constraint,
        "sentence_theme": None,
        "sentence_theme_topic": None,
    }

    if optional_constraint is None:
        user_prompt_params["sentence_theme_topic"], user_prompt_params["sentence_theme"] = (
            get_random_sentence_theme()
        )
    return user_prompt_params


async def generate_sentence(user_prompt_params: SentenceGeneratorParams) -> Sentence:
    # if settings.MOCK_AI:
    #     rprint("[yellow]Using MOCK_AI mode - returning mocked sentence[/yellow]")
    #     return get_mocked_sentence(level, tense)

    system_prompt = get_sentence_generator_system_prompt()
    user_prompt = get_sentence_generator_message_template() % user_prompt_params

    start_time = time.time()
    message = await anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=3000,
        temperature=1.0,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {
                    "type": "ephemeral",
                    # "ttl": "1h"
                },
            }
        ],
        messages=[
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "<sentence_planning>"},
        ],
    )

    _times.append(time.time() - start_time)
    average_time = sum(_times) / len(_times)
    group_panels = [
        Panel(
            Markdown(
                f"- Model: {ANTHROPIC_MODEL}\n"
                f"- Time taken: {_times[0]:.2f} seconds\n"
                f"- Average time: {average_time:.2f} seconds\n",
            )
        ),
        Panel(Pretty(user_prompt_params, expand_all=True), title="Prompt Parameters"),
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

    rprint(Panel(Group(*group_panels), title="Sentence Generation", border_style="green"))

    ukrainian_sentence = extract_tag_content(completion, "ukrainian_sentence")
    german_sentence = extract_tag_content(completion, "german_sentence")
    return Sentence(
        sentence_type=user_prompt_params["sentence_type"],
        ukrainian_sentence=ukrainian_sentence,
        german_sentence=german_sentence,
        tense=user_prompt_params["tense"],
        level=user_prompt_params["level"],
    )


def get_random_tense_for_level(level: DeutschLevel) -> DeutschTense:
    tenses = DEUTCH_LEVEL_TENSES[level]
    return random.choice(tenses)


def get_random_sentence_type() -> SentenceType:
    sentence_types = list(SentenceTypeProbabilities.keys())
    probabilities = list(SentenceTypeProbabilities.values())
    return random.choices(sentence_types, weights=probabilities, k=1)[0]


def get_random_sentence_theme() -> tuple[str, str]:
    sentence_themes = get_sentence_themes()
    key = random.choice(list(sentence_themes.keys()))
    return key, sentence_themes[key]


@cache
def get_sentence_generator_message_template() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("generate_sentence_user.txt"))


@cache
def get_sentence_generator_system_prompt() -> str:
    return load_prompt_template_from_file("generate_sentence_system.txt")


@cache
def get_sentence_themes() -> dict[str, str]:
    sentence_themes_str = load_prompt_template_from_file("sentence_themes.txt")
    sentence_themes_list = sentence_themes_str.split("\n\n")
    sentence_themes_list = [s.strip() for s in sentence_themes_list if s.strip()]
    key_parser_re = re.compile(r"^\*\*(.+?)\*\*")
    sentence_themes_dict = {}
    for theme_str in sentence_themes_list:
        match = key_parser_re.match(theme_str)
        if match:
            key = match.group(1).replace("_", " ")
            sentence_themes_dict[key] = theme_str
    return sentence_themes_dict


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
