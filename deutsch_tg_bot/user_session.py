from dataclasses import dataclass, field

from google.genai import chats

from deutsch_tg_bot.ai.translation_evalution import TranslationEvaluationResult
from deutsch_tg_bot.data_types import Sentence
from deutsch_tg_bot.deutsh_enums import DeutschLevel


@dataclass
class UserSession:
    sentences_history: list[Sentence] = field(default_factory=list)
    level: DeutschLevel | None = None
    sentence_constraint: str | None = None
    genai_chat: chats.AsyncChat | None = None
    last_translation_check_result: TranslationEvaluationResult | None = None
