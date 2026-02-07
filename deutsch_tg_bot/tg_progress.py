import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aiogram.types import Message


async def show_progress(message: Message, text: str) -> None:
    progress_message = await message.answer(f"<i>{text}</i>")
    i = 0
    try:
        while True:
            await asyncio.sleep(1)
            i += 1
            await progress_message.edit_text(f"<i>{text}{'.' * i}</i>")
            if i > 10:
                i = 0
    finally:
        await progress_message.delete()


@asynccontextmanager
async def progress(message: Message, text: str) -> AsyncGenerator[None, None]:
    task = asyncio.create_task(show_progress(message, text))
    try:
        yield
    except Exception as e:
        task.cancel()
        await message.answer(
            "Вибач, сталася помилка під час обробки твого запиту. Спробуй ще раз пізніше."
        )
        raise e
    finally:
        task.cancel()
