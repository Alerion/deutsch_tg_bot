from icecream import ic
from rich import print as rprint
from telegram import Update
from telegram.ext import Application

from deutsch_tg_bot.command_handlers.training import training_handler
from deutsch_tg_bot.config import settings


def start_bot() -> None:
    ic(settings.USERNAME_WHITELIST)
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(training_handler)
    rprint("Witing for commands...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
