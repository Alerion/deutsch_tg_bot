import anthropic
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from deutsch_tg_bot.command_handlers.start import start_command
from deutsch_tg_bot.config import settings

anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def start_bot() -> None:
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    print("Witing for commands...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)
