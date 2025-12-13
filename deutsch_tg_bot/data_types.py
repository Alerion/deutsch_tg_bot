from dataclasses import dataclass

from deutsch_tg_bot.deutsh_enums import DeutschLevel, DeutschTense, SentenceType


@dataclass
class Sentence:
    sentence_type: SentenceType
    ukrainian_sentence: str
    level: DeutschLevel
    tense: DeutschTense
    is_translation_correct: bool | None = None
