from copy import deepcopy

import anthropic
from rich import print as rprint

from deutsch_tg_bot.ai.anthropic_utils import (
    MessageDict,
)
from deutsch_tg_bot.config import settings

anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


async def answer_question(
    messages: list[MessageDict], user_question: str
) -> tuple[list[MessageDict], str]:
    messages = deepcopy(messages)
    messages.append({"role": "user", "content": user_question})

    if settings.MOCK_AI:
        completion = "Я не знаю відповіді на це питання."
        messages.append({"role": "assistant", "content": completion})
        return messages, completion

    message = await anthropic_client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=2000,
        temperature=0.7,
        messages=messages,
    )
    rprint("--- AI Answer Reply ---")
    rprint(message.content[0].text)
    rprint("-------- Usage --------")
    rprint(message.usage)
    completion = message.content[0].text.strip()
    messages.append({"role": "assistant", "content": completion})
    return messages, completion
