import time

from google.genai import chats
from rich import print as rprint
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.config import settings

# GOOGLE_MODEL = "gemini-2.5-flash"
GOOGLE_MODEL = "gemini-2.5-flash-lite"


async def answer_question(genai_chat: chats.AsyncChat, user_question: str) -> str:
    start_time = time.time()
    response = await genai_chat.send_message(user_question)
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
    print(ai_response)
    return ai_response
