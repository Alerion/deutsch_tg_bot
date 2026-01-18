from cyclopts import App

from deutsch_tg_bot.bot import start_bot

cli_app = App(
    name="deutsch_tg_bot",
    name_transform=lambda s: s,
)
cli_app.register_install_completion_command()

cli_app.command(start_bot)


if __name__ == "__main__":
    cli_app()
