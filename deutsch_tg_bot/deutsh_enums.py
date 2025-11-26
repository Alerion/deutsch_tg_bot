from enum import Enum


class DeutschLevel(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class DeutschTense(str, Enum):
    PRÄSENS = "Präsens"
    PERFEKT = "Perfekt"
    PRÄTERITUM = "Präteritum"
    PRÄSENS_FUTUR = "Präsens Futur"
    FUTUR1 = "Futur I"
    FUTUR2 = "Futur II"
    PLUSQUAMPERFEKT = "Plusquamperfekt"


DEUTCH_LEVEL_TENSES = {
    DeutschLevel.A1: [DeutschTense.PRÄSENS],
    DeutschLevel.A2: [DeutschTense.PRÄSENS, DeutschTense.PERFEKT],
    DeutschLevel.B1: [
        DeutschTense.PRÄSENS,
        DeutschTense.PERFEKT,
        DeutschTense.PRÄTERITUM,
    ],
    DeutschLevel.B2: [
        DeutschTense.PRÄSENS,
        DeutschTense.PERFEKT,
        DeutschTense.PRÄTERITUM,
        DeutschTense.PRÄSENS_FUTUR,
        DeutschTense.PLUSQUAMPERFEKT,
    ],
    DeutschLevel.C1: [
        DeutschTense.PRÄSENS,
        DeutschTense.PERFEKT,
        DeutschTense.PRÄTERITUM,
        DeutschTense.PRÄSENS_FUTUR,
        DeutschTense.PLUSQUAMPERFEKT,
        DeutschTense.FUTUR1,
    ],
    DeutschLevel.C2: [
        DeutschTense.PRÄSENS,
        DeutschTense.PERFEKT,
        DeutschTense.PRÄTERITUM,
        DeutschTense.PRÄSENS_FUTUR,
        DeutschTense.PLUSQUAMPERFEKT,
        DeutschTense.FUTUR1,
        DeutschTense.FUTUR2,
    ],
}
