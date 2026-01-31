"""AI module for checking grammar in user's German messages during roleplay."""

from google import genai
from pydantic import BaseModel, Field
from rich import print as rprint
from rich.panel import Panel
from rich.pretty import Pretty

from deutsch_tg_bot.config import settings
from deutsch_tg_bot.deutsh_enums import DeutschLevel

genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY).aio

GOOGLE_MODEL = "gemini-2.5-flash"


class GrammarCheckResult(BaseModel):
    """Result of grammar checking."""

    has_errors: bool = Field(
        description="True if the message contains grammar or vocabulary errors."
    )
    brief_feedback: str | None = Field(
        description="Brief, friendly feedback about errors. None if no errors.",
        default=None,
    )
    corrected_text: str | None = Field(
        description="The corrected version of the text. None if no errors.",
        default=None,
    )


GRAMMAR_CHECK_PROMPT = """Du bist ein Deutsch-Grammatikprüfer für ukrainische Lernende auf Niveau {level}.

Analysiere den folgenden deutschen Satz und prüfe auf:
1. Grammatikfehler (Kasus, Genus, Verbkonjugation, Wortstellung)
2. Rechtschreibfehler
3. Unpassende Wörter für das Niveau

WICHTIGE REGELN:
- Sei KURZ und FREUNDLICH - maximal 1-2 Sätze Feedback
- Erwähne NUR die wichtigsten Fehler
- Wenn der Satz verständlich und für das Niveau akzeptabel ist, melde KEINE Fehler
- Kleinere Tippfehler ignorieren, wenn der Sinn klar ist
- Feedback auf UKRAINISCH geben
- Sei ermutigend, nicht kritisch

Der zu prüfende Satz:
"{user_text}"

Kontext der Situation (für Verständnis):
{situation_context}"""


async def check_grammar_with_ai(
    user_text: str,
    level: DeutschLevel,
    situation_context: str,
) -> GrammarCheckResult:
    prompt = GRAMMAR_CHECK_PROMPT.format(
        level=level.value,
        user_text=user_text,
        situation_context=situation_context,
    )

    response = await genai_client.models.generate_content(
        model=GOOGLE_MODEL,
        config=genai.types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=GrammarCheckResult.model_json_schema(),
            temperature=0.3,  # Lower temperature for more consistent feedback
        ),
        contents=prompt,
    )

    response_text = (response.text or "").strip()

    try:
        result = GrammarCheckResult.model_validate_json(response_text)
    except Exception:
        # Fallback if parsing fails - assume no errors
        result = GrammarCheckResult(has_errors=False)

    if settings.SHOW_FULL_AI_RESPONSE:
        rprint(
            Panel(
                Pretty(
                    {
                        "user_text": user_text,
                        "level": level.value,
                        "has_errors": result.has_errors,
                        "feedback": result.brief_feedback,
                        "corrected": result.corrected_text,
                    },
                    expand_all=True,
                ),
                title="Grammar Check",
                border_style="yellow",
            )
        )

    return result
