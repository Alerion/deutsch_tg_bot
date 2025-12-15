import time
from functools import cache

from google import genai
from google.genai import chats
from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.ai.prompt_utils import (
    load_prompt_template_from_file,
    replace_promt_placeholder,
)
from deutsch_tg_bot.ai.translation_evalution import TranslationCheckResult
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.data_types import Sentence

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

GOOGLE_MODEL = "gemini-2.5-flash"
# GOOGLE_MODEL = "gemini-2.5-flash-lite"


async def answer_question_with_ai(
    user_question: str,
    sentence: Sentence,
    translation_check_result: TranslationCheckResult,
    genai_chat: chats.AsyncChat | None = None,
) -> tuple[str, chats.AsyncChat]:
    prompt_params = {
        "ukrainian_sentence": sentence.ukrainian_sentence,
        "evaluation_results": translation_check_result.evaluation_results,
        "level": sentence.level.value,
        "user_question": user_question,
    }
    answer_question_pompt = get_answer_question_prompt_template() % prompt_params

    if genai_chat is None:
        genai_chat = genai_client.chats.create(model=GOOGLE_MODEL)

    start_time = time.time()
    response = await genai_chat.send_message(answer_question_pompt)

    usage = response.usage_metadata
    ai_response = (response.text or "").strip()

    group_panels = [
        Panel(
            Markdown(
                f"- Model: {genai_chat._model}\n"
                f"- Time taken: {time.time() - start_time:.2f} seconds\n",
            )
        )
    ]
    if settings.SHOW_TOCKENS_USAGE:
        group_panels.append(Panel(Pretty(usage, expand_all=True), title="AI Usage"))

    rprint(Panel(Group(*group_panels), title="Question Answering", border_style="grey70"))

    return ai_response, genai_chat


@cache
def get_answer_question_prompt_template() -> str:
    return replace_promt_placeholder(load_prompt_template_from_file("answer_question.txt"))
