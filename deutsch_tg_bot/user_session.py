from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from google.genai import chats

from deutsch_tg_bot.data_types import Sentence
from deutsch_tg_bot.deutsh_enums import DeutschLevel, DeutschTense, SentenceType
from deutsch_tg_bot.utils.random_selector import BalancedRandomSelector

if TYPE_CHECKING:
    from deutsch_tg_bot.situation_training.situations import Situation
    from deutsch_tg_bot.translation_training.ai.translation_evaluation import (
        TranslationEvaluationResult,
    )


class TrainingType(str, Enum):
    """Available training types."""

    TRANSLATION = "translation"
    SITUATION = "situation"


@dataclass
class UserSession:
    # Common fields
    level: DeutschLevel | None = None
    training_type: TrainingType | None = None

    # Translation training fields
    sentences_history: list[Sentence] = field(default_factory=list)
    random_tense_selector: BalancedRandomSelector[DeutschTense] | None = None
    random_sentence_type_selector: BalancedRandomSelector[SentenceType] | None = None
    sentence_constraint: str | None = None
    genai_chat: chats.AsyncChat | None = None
    last_translation_check_result: TranslationEvaluationResult | None = None
    new_sentence_generation_task: asyncio.Task[Sentence] | None = None

    # Situation training fields
    current_situation: Situation | None = None
    situation_chat: chats.AsyncChat | None = None
    situation_message_count: int = 0
