"""Situation configuration for roleplay training."""

from dataclasses import dataclass

from deutsch_tg_bot.deutsh_enums import DeutschLevel


@dataclass
class Situation:
    """Configuration for a roleplay situation."""

    name_uk: str  # Ukrainian display name
    name_de: str  # German name
    character_role: str  # Character's role (e.g., "Arzt", "Verkäufer")
    user_role_uk: str  # User's role description in Ukrainian
    min_level: DeutschLevel  # German level for this situation
    scenario_prompt: str  # System prompt for the AI character
    opening_message_de: str  # Character's opening message in German
    opening_message_uk: str  # Ukrainian translation/explanation of opening
