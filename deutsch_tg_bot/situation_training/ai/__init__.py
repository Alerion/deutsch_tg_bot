"""AI modules for situation training."""

from deutsch_tg_bot.situation_training.ai.grammar_checker import check_grammar_with_ai
from deutsch_tg_bot.situation_training.ai.situation_agent import (
    generate_character_response,
    generate_situation_intro,
)

__all__ = [
    "check_grammar_with_ai",
    "generate_character_response",
    "generate_situation_intro",
]
