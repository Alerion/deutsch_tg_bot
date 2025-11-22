from dataclasses import dataclass, field
from enum import Enum

from telegram._user import User

from deutsch_tg_bot.deutsh_enums import DeutschLevel, DeutschTense


class State(Enum):
    IDLE = 1
    WAITING_FOR_TRANSLATION = 2
    WAITING_FOR_QUESTION = 3


@dataclass
class CurrentSentence:
    sentence: str
    tense: DeutschTense


@dataclass
class UserSession:
    state: State = State.IDLE
    current_sentence: CurrentSentence | None = None
    conversation_history: list[str] = field(default_factory=list)
    level: DeutschLevel | None = None


user_sessions: dict[int, UserSession] = {}


def get_user_session(user: User) -> UserSession:
    if user.id not in user_sessions:
        return reset_user_session(user)
    return user_sessions[user.id]


def reset_user_session(user: User) -> UserSession:
    user_sessions[user.id] = UserSession()
    return user_sessions[user.id]
