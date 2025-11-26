from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("До побачення! Щоб почати знову, введіть /start.")
    return ConversationHandler.END
