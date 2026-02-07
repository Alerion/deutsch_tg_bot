from telegram.ext import (
    ConversationHandler,
)

from deutsch_tg_bot.utils.handler_validation import ValidatedUpdate, check_handler_acces


@check_handler_acces
async def stop_command(vu: ValidatedUpdate) -> int:
    await vu.reply_text("До побачення! Щоб почати знову, введіть /start.")
    return ConversationHandler.END
