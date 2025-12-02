from dataclasses import dataclass, field

from deutsch_tg_bot.ai.anthropic_utils import MessageDict
from deutsch_tg_bot.deutsh_enums import DeutschLevel, DeutschTense


@dataclass
class Sentence:
    sentence: str
    level: DeutschLevel
    tense: DeutschTense
    is_translation_correct: bool | None = None


@dataclass
class UserSession:
    sentences_history: list[Sentence] = field(default_factory=list)
    level: DeutschLevel | None = None
    sentence_constraint: str | None = None
    conversation_messages: list[MessageDict] = field(default_factory=list)
