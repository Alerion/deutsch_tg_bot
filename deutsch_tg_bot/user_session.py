from dataclasses import dataclass, field
from enum import Enum

from telegram._user import User

from deutsch_tg_bot.deutsh_enums import DeutschLevel, DeutschTense


@dataclass
class CurrentSentence:
    sentence: str
    tense: DeutschTense


@dataclass
class UserSession:
    current_sentence: CurrentSentence | None = None
    conversation_history: list[CurrentSentence] = field(default_factory=list)
    level: DeutschLevel | None = None
