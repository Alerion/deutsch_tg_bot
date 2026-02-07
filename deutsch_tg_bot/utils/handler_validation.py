from functools import wraps
from typing import Callable

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from deutsch_tg_bot.config import settings


def check_handler_acces[R](
    handler_func: Callable[[Update, ContextTypes.DEFAULT_TYPE], R],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], R]:
    @wraps(handler_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> R | int:
        if update.message is None or update.message.text is None:
            raise ValueError("No message")

        if context.user_data is None:
            raise ValueError("No user data")

        if update.effective_user is None:
            raise ValueError("No effective user")

        username = update.effective_user.username
        if settings.USERNAME_WHITELIST and username not in settings.USERNAME_WHITELIST:
            if update.message is not None:
                await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.")
                return ConversationHandler.END
        return await handler_func(update, context)

    return wrapper
