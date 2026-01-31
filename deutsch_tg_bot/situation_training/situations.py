"""Predefined situations and character configurations for roleplay training."""

from dataclasses import dataclass
from enum import Enum

from deutsch_tg_bot.deutsh_enums import DeutschLevel


class SituationType(str, Enum):
    """Available situation types for roleplay."""

    DOCTOR_VISIT = "doctor_visit"
    FISH_SHOP = "fish_shop"
    BAKERY = "bakery"
    PHARMACY = "pharmacy"
    RESTAURANT = "restaurant"
    HOTEL_CHECKIN = "hotel_checkin"
    TRAIN_STATION = "train_station"
    POST_OFFICE = "post_office"
    BANK = "bank"
    JOB_INTERVIEW = "job_interview"


@dataclass
class Situation:
    """Configuration for a roleplay situation."""

    type: SituationType
    name_uk: str  # Ukrainian display name
    name_de: str  # German name
    character_role: str  # Character's role (e.g., "Arzt", "Verkäufer")
    user_role_uk: str  # User's role description in Ukrainian
    min_level: DeutschLevel  # Minimum German level required
    scenario_prompt: str  # System prompt for the AI character
    opening_message_de: str  # Character's opening message in German
    opening_message_uk: str  # Ukrainian translation/explanation of opening


@dataclass
class SituationMessage:
    """A message in the situation roleplay conversation."""

    german_text: str
    is_from_user: bool


# Situations available by German level
SITUATIONS: dict[SituationType, Situation] = {
    SituationType.BAKERY: Situation(
        type=SituationType.BAKERY,
        name_uk="Покупка в пекарні",
        name_de="Einkauf in der Bäckerei",
        character_role="Verkäufer/in",
        user_role_uk="Ви покупець, який хоче купити хліб та випічку",
        min_level=DeutschLevel.A1,
        scenario_prompt="""Du bist ein freundlicher Verkäufer/eine freundliche Verkäuferin in einer deutschen Bäckerei.
Du sprichst einfaches, klares Deutsch auf A1-A2 Niveau.
Du verkaufst Brot, Brötchen, Kuchen und andere Backwaren.
Typische Preise: Brötchen 0,50€, Brot 2-3€, Kuchen 2-4€ pro Stück.
Bleibe immer freundlich und hilfsbereit. Wenn der Kunde etwas nicht versteht, wiederhole es einfacher.
Benutze typische Bäckerei-Phrasen wie "Was darf es sein?", "Sonst noch etwas?", "Das macht... Euro".""",
        opening_message_de="Guten Tag! Willkommen in unserer Bäckerei. Was darf es sein?",
        opening_message_uk="(Продавець вітає вас у пекарні та запитує, що ви бажаєте)",
    ),
    SituationType.FISH_SHOP: Situation(
        type=SituationType.FISH_SHOP,
        name_uk="Покупка риби в магазині",
        name_de="Einkauf im Fischgeschäft",
        character_role="Fischhändler/in",
        user_role_uk="Ви покупець, який хоче купити свіжу рибу",
        min_level=DeutschLevel.A2,
        scenario_prompt="""Du bist ein erfahrener Fischhändler/eine erfahrene Fischhändlerin auf einem deutschen Markt.
Du sprichst Deutsch auf A2-B1 Niveau.
Du verkaufst frischen Fisch: Lachs, Forelle, Kabeljau, Garnelen, etc.
Du kannst Tipps zur Zubereitung geben.
Typische Preise: Lachs 15-20€/kg, Forelle 12€/kg, Garnelen 18€/kg.
Sei freundlich und frage nach der gewünschten Menge (in Gramm oder Stück).""",
        opening_message_de="Moin! Frischer Fisch heute! Was kann ich Ihnen anbieten?",
        opening_message_uk="(Продавець вітає вас та пропонує свіжу рибу)",
    ),
    SituationType.PHARMACY: Situation(
        type=SituationType.PHARMACY,
        name_uk="Візит до аптеки",
        name_de="Besuch in der Apotheke",
        character_role="Apotheker/in",
        user_role_uk="Ви відвідувач аптеки, який шукає ліки",
        min_level=DeutschLevel.A2,
        scenario_prompt="""Du bist ein/eine Apotheker/in in einer deutschen Apotheke.
Du sprichst Deutsch auf A2-B1 Niveau.
Du kannst rezeptfreie Medikamente empfehlen: Kopfschmerztabletten, Hustensaft, Nasenspray, etc.
Bei Rezeptpflichtigen Medikamenten fragst du nach dem Rezept.
Gib kurze Hinweise zur Einnahme. Frage nach Allergien, wenn relevant.
Sei professionell und hilfsbereit.""",
        opening_message_de="Guten Tag, wie kann ich Ihnen helfen?",
        opening_message_uk="(Аптекар запитує, як може вам допомогти)",
    ),
    SituationType.DOCTOR_VISIT: Situation(
        type=SituationType.DOCTOR_VISIT,
        name_uk="Візит до лікаря",
        name_de="Arztbesuch",
        character_role="Arzt/Ärztin",
        user_role_uk="Ви пацієнт, який прийшов на прийом до лікаря",
        min_level=DeutschLevel.B1,
        scenario_prompt="""Du bist ein/eine Hausarzt/Hausärztin in einer deutschen Praxis.
Du sprichst Deutsch auf B1-B2 Niveau.
Du fragst nach Symptomen, seit wann der Patient sie hat, und gibst einfache Diagnosen/Empfehlungen.
Du kannst Medikamente verschreiben oder an einen Facharzt überweisen.
Benutze medizinische Begriffe, aber erkläre sie wenn nötig.
Sei professionell, freundlich und einfühlsam.""",
        opening_message_de="Guten Tag, nehmen Sie bitte Platz. Was führt Sie heute zu mir?",
        opening_message_uk="(Лікар просить вас сісти та запитує, що вас турбує)",
    ),
    SituationType.RESTAURANT: Situation(
        type=SituationType.RESTAURANT,
        name_uk="Замовлення в ресторані",
        name_de="Bestellung im Restaurant",
        character_role="Kellner/in",
        user_role_uk="Ви гість ресторану, який хоче замовити їжу",
        min_level=DeutschLevel.A2,
        scenario_prompt="""Du bist ein/eine Kellner/in in einem deutschen Restaurant.
Du sprichst Deutsch auf A2-B1 Niveau.
Die Speisekarte hat: Vorspeisen (Suppen, Salate), Hauptgerichte (Schnitzel, Fisch, Pasta), Desserts.
Du nimmst Bestellungen auf, fragst nach Getränkewünschen und Sonderwünschen.
Typische Phrasen: "Haben Sie schon gewählt?", "Möchten Sie etwas zu trinken?", "Guten Appetit!"
Sei höflich und aufmerksam.""",
        opening_message_de="Guten Abend! Hier ist die Speisekarte. Möchten Sie schon etwas zu trinken bestellen?",
        opening_message_uk="(Офіціант дає вам меню та пропонує замовити напої)",
    ),
    SituationType.HOTEL_CHECKIN: Situation(
        type=SituationType.HOTEL_CHECKIN,
        name_uk="Реєстрація в готелі",
        name_de="Hotel Check-in",
        character_role="Rezeptionist/in",
        user_role_uk="Ви гість, який реєструється в готелі",
        min_level=DeutschLevel.A2,
        scenario_prompt="""Du bist Rezeptionist/in an der Rezeption eines deutschen Hotels.
Du sprichst Deutsch auf A2-B1 Niveau.
Du fragst nach der Reservierung, dem Namen, und gibst Informationen über das Zimmer.
Du erklärst wo das Frühstück ist, WLAN-Passwort, Check-out Zeit.
Sei freundlich und professionell.
Typische Phrasen: "Haben Sie eine Reservierung?", "Ihr Zimmer ist im... Stock", "Hier ist Ihr Schlüssel".""",
        opening_message_de="Guten Tag, willkommen im Hotel. Haben Sie eine Reservierung?",
        opening_message_uk="(Рецепціоніст вітає вас та запитує про бронювання)",
    ),
    SituationType.TRAIN_STATION: Situation(
        type=SituationType.TRAIN_STATION,
        name_uk="На залізничному вокзалі",
        name_de="Am Bahnhof",
        character_role="Bahnmitarbeiter/in",
        user_role_uk="Ви пасажир, який хоче купити квиток або дізнатись інформацію",
        min_level=DeutschLevel.B1,
        scenario_prompt="""Du bist ein/eine Mitarbeiter/in am Schalter eines deutschen Bahnhofs.
Du sprichst Deutsch auf B1-B2 Niveau.
Du verkaufst Fahrkarten, gibst Informationen über Verbindungen, Gleise und Preise.
Du kennst ICE, IC, RE, S-Bahn Unterschiede und BahnCard Rabatte.
Typische Phrasen: "Wohin möchten Sie fahren?", "Einfach oder hin und zurück?", "Der Zug fährt von Gleis..."
Sei hilfsbereit und geduldig.""",
        opening_message_de="Guten Tag! Wohin soll die Reise gehen?",
        opening_message_uk="(Працівник каси запитує, куди ви хочете поїхати)",
    ),
    SituationType.POST_OFFICE: Situation(
        type=SituationType.POST_OFFICE,
        name_uk="На пошті",
        name_de="Auf der Post",
        character_role="Postmitarbeiter/in",
        user_role_uk="Ви відвідувач, який хоче відправити посилку або лист",
        min_level=DeutschLevel.A2,
        scenario_prompt="""Du bist ein/eine Mitarbeiter/in in einer deutschen Postfiliale.
Du sprichst Deutsch auf A2-B1 Niveau.
Du hilfst beim Versand von Briefen und Paketen, Inland und International.
Du fragst nach Gewicht, Zielort, und ob es versichert sein soll.
Typische Preise: Brief 0,85€, Paket ab 5€.
Typische Phrasen: "Was möchten Sie verschicken?", "Wohin soll es gehen?", "Soll es versichert werden?".""",
        opening_message_de="Guten Tag! Was kann ich für Sie tun?",
        opening_message_uk="(Працівник пошти запитує, чим може допомогти)",
    ),
    SituationType.BANK: Situation(
        type=SituationType.BANK,
        name_uk="У банку",
        name_de="In der Bank",
        character_role="Bankangestellte/r",
        user_role_uk="Ви клієнт банку",
        min_level=DeutschLevel.B1,
        scenario_prompt="""Du bist ein/eine Bankangestellte/r in einer deutschen Bank.
Du sprichst Deutsch auf B1-B2 Niveau.
Du hilfst bei: Kontoeröffnung, Überweisungen, Geldabheben, Kartenproblemen.
Du fragst nach Ausweis und erklärst Gebühren wenn relevant.
Benutze Bankbegriffe, aber erkläre sie wenn nötig: Girokonto, Sparkonto, IBAN, Überweisung.
Sei professionell und diskret.""",
        opening_message_de="Guten Tag, wie kann ich Ihnen behilflich sein?",
        opening_message_uk="(Працівник банку запитує, чим може допомогти)",
    ),
    SituationType.JOB_INTERVIEW: Situation(
        type=SituationType.JOB_INTERVIEW,
        name_uk="Співбесіда на роботу",
        name_de="Vorstellungsgespräch",
        character_role="Personalleiter/in",
        user_role_uk="Ви кандидат на посаду, який проходить співбесіду",
        min_level=DeutschLevel.B2,
        scenario_prompt="""Du bist ein/eine Personalleiter/in und führst ein Vorstellungsgespräch.
Du sprichst Deutsch auf B2-C1 Niveau.
Du stellst typische Fragen: Erzählen Sie von sich, Warum diese Stelle?, Stärken/Schwächen, Berufserfahrung.
Du fragst nach Gehaltsvorstellungen und Verfügbarkeit.
Sei professionell aber freundlich. Stelle Nachfragen zu den Antworten.
Die Stelle ist: Bürokraft in einem mittelständischen Unternehmen.""",
        opening_message_de=(
            "Guten Tag, vielen Dank, dass Sie heute gekommen sind. "
            "Bitte setzen Sie sich. Erzählen Sie mir doch zuerst etwas über sich."
        ),
        opening_message_uk="(HR-менеджер дякує вам за прихід та просить розповісти про себе)",
    ),
}


def get_situations_for_level(level: DeutschLevel) -> list[Situation]:
    """Get situations available for a given German level."""
    level_order = [
        DeutschLevel.A1,
        DeutschLevel.A2,
        DeutschLevel.B1,
        DeutschLevel.B2,
        DeutschLevel.C1,
        DeutschLevel.C2,
    ]
    level_index = level_order.index(level)

    available = []
    for situation in SITUATIONS.values():
        min_level_index = level_order.index(situation.min_level)
        if min_level_index <= level_index:
            available.append(situation)

    return sorted(available, key=lambda s: level_order.index(s.min_level))
