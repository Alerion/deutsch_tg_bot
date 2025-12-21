import random
import re
import time
from functools import cache
from itertools import cycle
from typing import Any, TypedDict

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
from deutsch_tg_bot.deutsh_enums import (
    DeutschLevel,
    DeutschTense,
    SentenceType,
    SentenceTypeProbabilities,
)

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

GOOGLE_MODEL = "gemini-2.5-flash"
# GOOGLE_MODEL = "gemini-2.5-flash-lite"

_times: list[float] = []


class GenerateSentenceResponse(BaseModel):
    planning: str = Field(
        description="Detailed step-by-step thinking process (Step 1-8). Analyze level, tense, and constraints here."
    )
    ukrainian_sentence: str = Field(
        description="The final Ukrainian sentence for the user to translate."
    )
    german_reference: str = Field(
        description="The ideal German translation focusing on the specific grammar rule."
    )
    grammar_explanation: str = Field(
        description="Short explanation of why this sentence fits the level/tense."
    )


class SentenceGeneratorParams(TypedDict):
    level: DeutschLevel
    tense: DeutschTense
    sentence_type: SentenceType
    recent_sentences: str
    optional_constraint: str | None
    sentence_theme: str | None
    sentence_theme_topic: str | None


async def generate_sentence_with_ai(user_prompt_params: SentenceGeneratorParams) -> Sentence:
    sentence_generator_prompt = get_sentence_generator_prompt() % user_prompt_params

    start_time = time.time()
    response = await genai_client.models.generate_content(
        model=GOOGLE_MODEL,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=GenerateSentenceResponse.model_json_schema(),
            temperature=0.7,
        ),
        contents=sentence_generator_prompt,
    )

    usage = response.usage_metadata
    generate_sentence_response = GenerateSentenceResponse.model_validate_json(response.text or "")

    _times.append(time.time() - start_time)
    average_time = sum(_times) / len(_times)
    group_panels = [
        Panel(
            Markdown(
                f"- Model: {GOOGLE_MODEL}\n"
                f"- Time taken: {_times[0]:.2f} seconds\n"
                f"- Average time: {average_time:.2f} seconds\n",
            )
        ),
        Panel(Pretty(user_prompt_params, expand_all=True), title="Prompt Parameters"),
    ]
    if settings.SHOW_TOCKENS_USAGE:
        group_panels.append(Panel(Pretty(usage, expand_all=True), title="AI Usage"))

    if settings.SHOW_FULL_AI_RESPONSE:
        group_panels.append(
            Panel(
                Pretty(generate_sentence_response, expand_all=True),
                title="Full AI Response",
            )
        )

    rprint(Panel(Group(*group_panels), title="Sentence Generation", border_style="green"))

    return Sentence(
        sentence_type=user_prompt_params["sentence_type"],
        ukrainian_sentence=generate_sentence_response.ukrainian_sentence,
        german_sentence=generate_sentence_response.german_reference,
        tense=user_prompt_params["tense"],
        level=user_prompt_params["level"],
    )


def get_sentence_generator_params(
    level: DeutschLevel,
    tense: DeutschTense,
    sentences_history: list[Sentence],
    optional_constraint: str | None = None,
    recent_sentences_count: int = 3,
) -> SentenceGeneratorParams:
    recent_sentences: list[str] = [
        sentence.german_sentence for sentence in sentences_history[-recent_sentences_count:]
    ]

    user_prompt_params: SentenceGeneratorParams = {
        "level": level,
        "tense": tense,
        "sentence_type": get_random_sentence_type(),
        "optional_constraint": optional_constraint,
        "recent_sentences": "\n".join(recent_sentences),
        "sentence_theme": None,
        "sentence_theme_topic": None,
    }

    if optional_constraint is None:
        user_prompt_params["sentence_theme_topic"], user_prompt_params["sentence_theme"] = (
            get_random_sentence_theme()
        )
    return user_prompt_params


def get_random_sentence_type() -> SentenceType:
    sentence_types = list(SentenceTypeProbabilities.keys())
    probabilities = list(SentenceTypeProbabilities.values())
    return random.choices(sentence_types, weights=probabilities, k=1)[0]


def get_random_sentence_theme() -> tuple[str, str]:
    sentence_themes = get_sentence_themes()
    key = random.choice(list(sentence_themes.keys()))
    return key, sentence_themes[key]


@cache
def get_sentence_generator_prompt() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("generate_sentence.txt"))


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
    # TODO
    return {}


def get_mocked_sentence(user_prompt_params: SentenceGeneratorParams) -> Sentence:
    ukrainian_sentence = next(mocked_ukrainian_sentences)
    german_sentence = next(mocked_german_sentences)
    return Sentence(
        sentence_type=user_prompt_params["sentence_type"],
        ukrainian_sentence=ukrainian_sentence,
        german_sentence=german_sentence,
        tense=user_prompt_params["tense"],
        level=user_prompt_params["level"],
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

mocked_german_sentences = cycle(
    [
        "Das ist mein Buch.",
        "Sie geht zur Schule.",
        "Wir spielen Fußball.",
        "Sie wohnen in einer großen Stadt.",
        "Ich lese gerne Bücher.",
    ]
)
