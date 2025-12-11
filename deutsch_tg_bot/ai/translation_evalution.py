import time
from dataclasses import dataclass
from functools import cache

from google import genai
from google.genai import chats
from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.ai.prompt_utils import (
    extract_tag_content,
    load_prompt_template_from_file,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.user_session import Sentence

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

# GOOGLE_MODEL = "gemini-2.5-flash"
GOOGLE_MODEL = "gemini-2.5-flash-lite"


@dataclass
class TranslationCheckResult:
    genai_chat: chats.AsyncChat
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

    start_time = time.time()
    genai_chat = genai_client.chats.create(model=GOOGLE_MODEL)
    response = await genai_chat.send_message(evaluate_prompt)
    usage = response.usage_metadata
    ai_response = response.text.strip()

    # response1 = await genai_chat.send_message("Поясни мені структуру речення.")
    # print(response1.text.strip())

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
        print(ai_response)
        group_panels.append(
            Panel(
                Markdown(ai_response),
                title="Full AI Response",
            )
        )

    rprint(Panel(Group(*group_panels), title="Translation Evaluation", border_style="blue"))

    correct_translation = extract_tag_content(ai_response, "correct_translation")
    explanation = extract_tag_content(ai_response, "explanation")
    return TranslationCheckResult(
        genai_chat=genai_chat,
        correct_translation=correct_translation,
        explanation=explanation,
    )


@cache
def get_translation_evaluation_prompt_template() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("translation_evaluation.txt"))
