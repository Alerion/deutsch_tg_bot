from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from functools import wraps
from typing import Any, cast

from telegram import Message, Update, User
from telegram.ext import ContextTypes, ConversationHandler

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.user_session import UserSession


@dataclass
class ValidatedUpdate:
    update: Update
    message: Message
    message_text: str
    user: User
    session: UserSession


type ValidatedHandler = Callable[[ValidatedUpdate], Coroutine[Any, Any, int]]
type RawHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, int]]


def check_handler_acces(handler_func: ValidatedHandler) -> RawHandler:
    @wraps(handler_func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if update.message is None or update.message.text is None:
            raise ValueError("No message")

        if context.user_data is None:
            raise ValueError("No user data")

        if update.effective_user is None:
            raise ValueError("No effective user")

        username = update.effective_user.username
        if settings.USERNAME_WHITELIST and username not in settings.USERNAME_WHITELIST:
            await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.")
            return ConversationHandler.END

        if "session" in context.user_data:
            session = cast(UserSession, context.user_data["session"])
        else:
            session = UserSession()

        validated_update = ValidatedUpdate(
            update=update,
            message=update.message,
            message_text=update.message.text.strip(),
            user=update.effective_user,
            session=session,
        )
        response = await handler_func(validated_update)
        context.user_data["session"] = validated_update.session
        return response

    return wrapper
