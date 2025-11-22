import anthropic
from rich import print as rprint
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from deutsch_tg_bot.command_handlers.start import training_handler
from deutsch_tg_bot.config import settings

anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def start_bot() -> None:
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(training_handler)
    rprint("Witing for commands...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
