import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from deutsch_tg_bot.utils.handler_validation import ValidatedUpdate


async def show_progress(vu: ValidatedUpdate, text: str) -> None:
    progress_message = await vu.message.reply_text(f"_{text}_", parse_mode="Markdown")
    i = 0
    try:
        while True:
            await asyncio.sleep(1)
            i += 1
            await progress_message.edit_text(f"_{text}{'.' * i}_", parse_mode="Markdown")
            if i > 10:
                i = 0
    finally:
        await progress_message.delete()


@asynccontextmanager
async def progress(vu: ValidatedUpdate, text: str) -> AsyncGenerator[None, None]:
    task = asyncio.create_task(show_progress(vu, text))
    try:
        yield
    except Exception as e:
        task.cancel()
        await vu.message.reply_text(
            "Вибач, сталася помилка під час обробки твого запиту. Спробуй ще раз пізніше."
        )
        raise e
    finally:
        task.cancel()
