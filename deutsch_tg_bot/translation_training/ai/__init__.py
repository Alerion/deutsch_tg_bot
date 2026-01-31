"""AI modules for translation training."""

from deutsch_tg_bot.translation_training.ai.question_answering import answer_question_with_ai
from deutsch_tg_bot.translation_training.ai.sentence_generator import (
    generate_sentence_with_ai,
    get_sentence_generator_params,
)
from deutsch_tg_bot.translation_training.ai.translation_evaluation import (
    TranslationEvaluationResult,
    evaluate_translation_with_ai,
)

__all__ = [
    "answer_question_with_ai",
    "generate_sentence_with_ai",
    "get_sentence_generator_params",
    "TranslationEvaluationResult",
    "evaluate_translation_with_ai",
]
