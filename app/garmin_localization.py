"""Bilingual display names for Garmin FIT exercise enum values.

German labels are UI aids only; Garmin still receives the unchanged numeric
(category, subtype) pair. Keep the official English enum name accessible for
every item. Exact German translations override compositional terms. Unknown
terms remain in English rather than guessing at a different movement.
"""
from garmin_catalog_part1 import ROWS as _R1
from garmin_catalog_part2 import ROWS as _R2
from garmin_catalog_part3 import ROWS as _R3
from garmin_catalog_part4 import ROWS as _R4
from garmin_catalog_part5 import ROWS as _R5

# Explicit, human-reviewed names for common exercise categories and movements.
DE_EXACT = {
    (0, 1): "Langhantel-Bankdrücken",
    (0, 6): "Kurzhantel-Bankdrücken",
    (0, 8): "Schrägbankdrücken mit Langhantel",
    (0, 9): "Schrägbankdrücken mit Kurzhanteln",
    (2, 12): "Hampelmänner / Sternsprünge",
    (2, 13): "Hampelmänner mit Zusatzgewicht",
    (8, 0): "Kreuzheben mit Langhantel",
    (8, 2): "Kreuzheben mit Kurzhanteln",
    (8, 15): "Sumo-Kreuzheben",
    (8, 23): "Rumänisches Kreuzheben",
    (28, 6): "Kniebeuge mit Langhantel",
    (28, 8): "Frontkniebeuge mit Langhantel",
    (21, 38): "Klimmzug",
    (21, 43): "Klimmzug mit neutralem Griff",
    (19, 43): "Unterarmstütz / Plank",
    (23, 1): "Kabelrudern stehend",
    (23, 18): "Kabelrudern sitzend",
    (23, 2): "Kurzhantelrudern",
    (23, 13): "Einarmiges Kurzhantelrudern",
    (24, 4): "Schulterdrücken mit Langhantel",
    (24, 15): "Überkopfdrücken mit Kurzhanteln",
    (24, 17): "Schulterdrücken sitzend mit Kurzhanteln",
    (31, 31): "Bizepsdehnung",
    (31, 38): "Katze-Kuh-Dehnung",
    (31, 39): "Kindhaltung",
    (31, 45): "Hüftbeugerdehnung",
    (31, 46): "Latissimusdehnung",
}

# Multiword exercise terms first; all terms are directly meaningful in German.
PHRASES_DE = (
    ("BARBELL BENCH PRESS", "LANGHANTEL-BANKDRÜCKEN"),
    ("DUMBBELL BENCH PRESS", "KURZHANTEL-BANKDRÜCKEN"),
    ("BARBELL DEADLIFT", "LANGHANTEL-KREUZHEBEN"),
    ("ROMANIAN DEADLIFT", "RUMÄNISCHES KREUZHEBEN"),
    ("DUMBBELL DEADLIFT", "KURZHANTEL-KREUZHEBEN"),
    ("BENCH PRESS", "BANKDRÜCKEN"),
    ("CHEST PRESS", "BRUSTDRÜCKEN"),
    ("SHOULDER PRESS", "SCHULTERDRÜCKEN"),
    ("PUSH UP", "LIEGESTÜTZ"),
    ("PULL UP", "KLIMMZUG"),
    ("LAT PULLDOWN", "LATZIEHEN"),
    ("HIGH KNEES", "HOHE KNIE"),
    ("CABLE ROW", "KABELRUDERN"),
    ("REVERSE FLY", "REVERSE FLY"),
    ("JUMPING JACKS", "HAMPELMÄNNER"),
    ("SQUAT JUMP", "KNIEBEUGENSPRUNG"),
    ("SINGLE ARM", "EINARMIG"),
    ("ONE ARM", "EINARMIG"),
    ("SINGLE LEG", "EINBEINIG"),
    ("ONE LEG", "EINBEINIG"),
    ("DOUBLE ARM", "BEIDARMIG"),
    ("DUAL HANDLE", "DOPPELGRIFF"),
    ("BENT OVER", "VORGEBEUGT"),
    ("WIDE GRIP", "BREITER GRIFF"),
    ("NARROW GRIP", "ENGER GRIFF"),
    ("CLOSE GRIP", "ENGER GRIFF"),
    ("NEUTRAL GRIP", "NEUTRALER GRIFF"),
    ("BODY WEIGHT", "EIGENGEWICHT"),
    ("BODYWEIGHT", "EIGENGEWICHT"),
    ("RESISTANCE BAND", "WIDERSTANDSBAND"),
    ("MEDICINE BALL", "MEDIZINBALL"),
    ("HIP FLEXOR", "HÜFTBEUGER"),
    ("HAMSTRING", "BEINRÜCKSEITE"),
)

WORDS_DE = {
    "BARBELL": "LANGHANTEL",
    "DUMBBELL": "KURZHANTEL",
    "KETTLEBELL": "KETTLEBELL",
    "CABLE": "KABELZUG",
    "MACHINE": "MASCHINE",
    "SMITH": "SMITH",
    "BENCH": "BANK",
    "PRESS": "DRÜCKEN",
    "CHEST": "BRUST",
    "FLY": "FLIEGENDE",
    "FLYE": "FLIEGENDE",
    "ROW": "RUDERN",
    "PULLDOWN": "LATZIEHEN",
    "PULL": "ZIEHEN",
    "PUSH": "DRÜCKEN",
    "DEADLIFT": "KREUZHEBEN",
    "SQUAT": "KNIEBEUGE",
    "LUNGE": "AUSFALLSCHRITT",
    "SHOULDER": "SCHULTER",
    "BICEPS": "BIZEPS",
    "TRICEPS": "TRIZEPS",
    "CURL": "CURL",
    "CURLS": "CURLS",
    "STRETCH": "DEHNUNG",
    "PLANK": "PLANK",
    "CORE": "RUMPF",
    "CRUNCH": "CRUNCH",
    "SIT": "SITZEN",
    "UP": "HOCH",
    "RAISE": "HEBEN",
    "RAISES": "HEBEN",
    "LEG": "BEIN",
    "LEGS": "BEINE",
    "ARM": "ARM",
    "ARMS": "ARME",
    "CALF": "WADE",
    "CALVES": "WADEN",
    "HIP": "HÜFTE",
    "GLUTE": "GESÄSS",
    "GLUTES": "GESÄSS",
    "LATERAL": "SEITLICH",
    "FRONT": "VORNE",
    "BACK": "RÜCKEN",
    "BACKWARD": "RÜCKWÄRTS",
    "REVERSE": "UMGEKEHRT",
    "INCLINE": "SCHRÄG",
    "DECLINE": "NEGATIV",
    "FLAT": "FLACH",
    "SEATED": "SITZEND",
    "STANDING": "STEHEND",
    "LYING": "LIEGEND",
    "KNEELING": "KNIEND",
    "WALKING": "GEHEND",
    "RUNNING": "LAUFEND",
    "JUMP": "SPRUNG",
    "JUMPING": "SPRINGEND",
    "STEP": "SCHRITT",
    "SIDE": "SEITE",
    "SIDEWAYS": "SEITWÄRTS",
    "WIDE": "BREIT",
    "NARROW": "ENG",
    "GRIP": "GRIFF",
    "ALTERNATING": "ABWECHSELND",
    "WEIGHTED": "MIT ZUSATZGEWICHT",
    "ASSISTED": "UNTERSTÜTZT",
    "SINGLE": "EINZELN",
    "DOUBLE": "DOPPELT",
    "ROTATION": "DREHUNG",
    "TWIST": "DREHUNG",
    "BALANCE": "BALANCE",
    "EXTENSION": "STRECKEN",
    "FLEXION": "BEUGEN",
    "ADDUCTION": "ADDUKTION",
    "ABDUCTION": "ABDUKTION",
    "ABDOMINAL": "BAUCH",
    "ABDOMINALS": "BAUCH",
    "HINGE": "HÜFTBEUGE",
    "SWISS": "SWISS",
    "BALL": "BALL",
    "FOAM": "SCHAUMSTOFF",
    "ROLLER": "ROLLE",
    "BAND": "BAND",
    "WITH": "MIT",
    "ON": "AUF",
    "AND": "UND",
    "TO": "ZU",
    "FROM": "VON",
    "OVER": "ÜBER",
    "UNDER": "UNTER",
    "BEHIND": "HINTER",
    "FORWARD": "VORWÄRTS",
    "FULL": "VOLL",
    "PARTIAL": "TEILWEISE",
    "ISOMETRIC": "ISOMETRISCH",
    "SUMO": "SUMO",
    "ROMANIAN": "RUMÄNISCH",
    "LAT": "LATISSIMUS",
    "TRAP": "TRAPEZMUSKEL",
    "UPPER": "OBER",
    "LOWER": "UNTER",
    "INNER": "INNEN",
    "OUTER": "AUSSEN",
    "HAND": "HAND",
    "HANDS": "HÄNDE",
    "KNEE": "KNIE",
    "KNEES": "KNIE",
    "ANKLE": "KNÖCHEL",
    "NECK": "NACKEN",
    "ELBOW": "ELLBOGEN",
    "FOOT": "FUSS",
    "FEET": "FÜSSE",
    "WALL": "WAND",
    "FLOOR": "BODEN",
    "STABILITY": "STABILITÄT",
    "CARDIO": "CARDIO",
    "BIKE": "FAHRRAD",
    "ROWER": "RUDERGERÄT",
    "TREADMILL": "LAUFBAND",
    "TRX": "TRX",
}


def german_exercise_name(english_enum, category, subtype):
    """Render German where verified terms are available; leave unfamiliar ones English."""
    pair = (int(category), int(subtype))
    if pair in DE_EXACT:
        return DE_EXACT[pair]
    words = str(english_enum).replace("_", " ").upper().split()
    if not words:
        return ""
    # Translate known compound expressions before single words.
    text = " ".join(words)
    for english, german in PHRASES_DE:
        text = text.replace(english, german.replace(" ", "~"))
    translated = [WORDS_DE.get(word, word) for word in text.split()]
    return " ".join(translated).replace("~", " ").title()


def english_exercise_name(english_enum):
    """The immutable Garmin enum is authoritative for the exercise identity."""
    return str(english_enum).replace("_", " ").title()
