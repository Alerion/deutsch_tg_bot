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
    from deutsch_tg_bot.situation_training.scene_state import SceneState
    from deutsch_tg_bot.situation_training.situations import Situation
    from deutsch_tg_bot.translation_training.ai.translation_evaluation import (
        TranslationEvaluationResult,
    )


class TrainingType(str, Enum):
    TRANSLATION = "translation"
    SITUATION = "situation"


@dataclass
class SentenceTranslationState:
    random_tense_selector: BalancedRandomSelector[DeutschTense]
    random_sentence_type_selector: BalancedRandomSelector[SentenceType]
    sentences_history: list[Sentence] = field(default_factory=list)
    sentence_constraint: str | None = None
    genai_chat: chats.AsyncChat | None = None
    last_translation_check_result: TranslationEvaluationResult | None = None
    new_sentence_generation_task: asyncio.Task[Sentence] | None = None


@dataclass
class SituationTrainingState:
    current_situation: Situation
    situation_chat: chats.AsyncChat
    scene_state: SceneState
    situation_message_count: int = 0
    last_narrator_event_index: int = 0
    recent_dialogue: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class UserSession:
    deutsch_level: DeutschLevel

    sentence_translation: SentenceTranslationState | None = None
    situation_training: SituationTrainingState | None = None
