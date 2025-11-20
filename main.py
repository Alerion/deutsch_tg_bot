import typer

from deutsch_tg_bot.bot import start_bot

app = typer.Typer()


# python -m main start_bot
app.command("start_bot")(start_bot)

if __name__ == "__main__":
    app()
