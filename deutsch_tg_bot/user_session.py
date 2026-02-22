from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

from google.genai import chats

from deutsch_tg_bot.data_types import Sentence
from deutsch_tg_bot.deutsh_enums import DeutschTense, SentenceType
from deutsch_tg_bot.utils.random_selector import BalancedRandomSelector

if TYPE_CHECKING:
    from deutsch_tg_bot.situation_training.ai.data_types import GameState, NPCState, PlayerState
    from deutsch_tg_bot.translation_training.ai.translation_evaluation import (
        TranslationEvaluationResult,
    )


class HistoryMessage(TypedDict):
    sender: str  # "player", "narrator" or npc_id
    text: str


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
    game_state: GameState
    npc_states: list[NPCState]
    player_state: PlayerState

    messages_history: list[HistoryMessage] = field(default_factory=list)

    player_message_count: int = 0
    last_narrator_event_index: int = 0
