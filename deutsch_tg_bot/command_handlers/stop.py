from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None or update.message.text is None:
        raise ValueError("Expected a message in update")

    await update.message.reply_text("До побачення! Щоб почати знову, введіть /start.")
    return ConversationHandler.END
