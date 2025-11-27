from copy import deepcopy
from dataclasses import dataclass

import anthropic
from rich import print as rprint

from deutsch_tg_bot.ai.anthropic_utils import (
    MessageDict,
    extract_tag_content,
    replace_promt_placeholder,
)
from deutsch_tg_bot.config import settings
from deutsch_tg_bot.user_session import Sentence

anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def answer_question(
    messages: list[MessageDict], user_question: str
) -> tuple[list[MessageDict], str]:
    messages = deepcopy(messages)
    messages.append({"role": "user", "content": user_question})
    response = anthropic_client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=1000,
        temperature=0.7,
        messages=messages,
    )
    rprint("--- AI Answer Reply ---")
    rprint(response.content[0].text)
    completion = response.content[0].text.strip()
    messages.append({"role": "assistant", "content": completion})
    return messages, completion
