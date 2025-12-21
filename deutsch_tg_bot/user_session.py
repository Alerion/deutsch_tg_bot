from __future__ import annotations

from dataclasses import dataclass, field

from google.genai import chats

from deutsch_tg_bot.ai.translation_evalution import TranslationEvaluationResult
from deutsch_tg_bot.data_types import Sentence
from deutsch_tg_bot.deutsh_enums import DeutschLevel, DeutschTense, SentenceType
from deutsch_tg_bot.utils.random_selector import BalancedRandomSelector


@dataclass
class UserSession:
    sentences_history: list[Sentence] = field(default_factory=list)
    random_tense_selector: BalancedRandomSelector[DeutschTense] | None = None
    random_sentence_type_selector: BalancedRandomSelector[SentenceType] | None = None
    level: DeutschLevel | None = None
    sentence_constraint: str | None = None
    genai_chat: chats.AsyncChat | None = None
    last_translation_check_result: TranslationEvaluationResult | None = None
