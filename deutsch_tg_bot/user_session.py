from dataclasses import dataclass, field

from deutsch_tg_bot.deutsh_enums import DeutschLevel, DeutschTense


@dataclass
class Sentence:
    sentence: str
    tense: DeutschTense


@dataclass
class UserSession:
    conversation_history: list[Sentence] = field(default_factory=list)
    level: DeutschLevel | None = None
    constraint: str | None = None
