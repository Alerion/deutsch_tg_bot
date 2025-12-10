import time
from copy import deepcopy

import anthropic
from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.ai.anthropic_utils import (
    MessageDict,
)
from deutsch_tg_bot.config import settings

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# https://docs.anthropic.com/en/docs/about-claude/models/overview#model-names
ANTHROPIC_MODEL = "claude-haiku-4-5"


async def answer_question(
    messages: list[MessageDict], user_question: str
) -> tuple[list[MessageDict], str]:
    messages = deepcopy(messages)
    messages.append({"role": "user", "content": user_question})

    if settings.MOCK_AI:
        completion = "Я не знаю відповіді на це питання."
        messages.append({"role": "assistant", "content": completion})
        return messages, completion

    start_time = time.time()
    message = await anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        temperature=0.7,
        messages=messages,
    )

    group_panels = [
        Panel(
            Markdown(
                f"- Model: {ANTHROPIC_MODEL}\n"
                f"- Time taken: {time.time() - start_time:.2f} seconds\n",
                f"- Messages sent: {len(messages)}",
            )
        )
    ]
    if settings.SHOW_TOCKENS_USAGE:
        group_panels.append(Panel(Pretty(message.usage, expand_all=True), title="AI Usage"))

    rprint(Panel(Group(*group_panels), title="Question Answering", border_style="grey70"))

    completion = message.content[0].text.strip()
    messages.append({"role": "assistant", "content": completion})
    return messages, completion
