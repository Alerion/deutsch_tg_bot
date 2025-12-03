import typer
from rich import print as rprint

from deutsch_tg_bot.ai.sentence_generator import get_system_prompt_token_count
from deutsch_tg_bot.bot import start_bot
from deutsch_tg_bot.utils.asyncio import async_to_sync

app = typer.Typer()


@app.command("count_tokens")
@async_to_sync
async def count_tokens() -> None:
    response = await get_system_prompt_token_count()
    rprint(response)


# python -m main start_bot
app.command("start_bot")(start_bot)

if __name__ == "__main__":
    app()
