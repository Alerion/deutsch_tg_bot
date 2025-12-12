import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from telegram import Update


async def show_progress(update: Update, text: str) -> None:
    if update.message is None:
        return

    progress_message = await update.message.reply_text(f"_{text}_", parse_mode="Markdown")
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
async def progress(update: Update, text: str) -> AsyncGenerator[None, None]:
    task = asyncio.create_task(show_progress(update, text))
    try:
        yield
    except Exception as e:
        task.cancel()
        if update.message is not None:
            await update.message.reply_text(
                "Вибач, сталася помилка під час обробки твого запиту. Спробуй ще раз пізніше."
            )
        raise e
    finally:
        task.cancel()
