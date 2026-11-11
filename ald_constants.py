"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STUFEN = ("A", "B", "C")
STUFEN_NAMEN = {"A": "A – paarweise", "B": "B – Bounds (Hall-Intervalle)", "C": "C – Régin (Matching)"}
STUFEN_KURZ = {"A": "A paarweise", "B": "B Bounds", "C": "C Régin"}

BEISPIEL_H2 = "H2 – Löcher in den Domänen"
BEISPIEL_H1 = "H1 – Hall-Verletzung (vier Variablen, drei Werte)"
BEISPIEL_H3 = "H3 – Rotationsplan 4 × 4 mit Vorbelegungen"
BEISPIEL_EIGEN = "Eigene Domänen"
BEISPIELE = (BEISPIEL_H2, BEISPIEL_H1, BEISPIEL_H3, BEISPIEL_EIGEN)
EIGENE_STANDARD = "1 3; 1 3; 1 2 3; 2 3 4"   # H2 als Ausgangspunkt der eigenen Domänen
EIGENE_VAR_MIN, EIGENE_VAR_MAX = 2, 8       # Zahl der Variablen im Editor
EIGENE_WERT_MIN, EIGENE_WERT_MAX = 1, 8     # Wertebereich im Editor
TEXT_MAX = 200                              # Länge des Editor-Textes

BUDGET_OPTIONEN = (1000, 5000, 20000, 50000)
DEFAULT_BUDGET = 50000
DEFAULT_STUFE = "C"
SEED_MAX, DEFAULT_SEED = 999999, 0

HALL_K_MIN, HALL_K_MAX, DEFAULT_HALL_K = 3, 9, 4
HALL_M_MIN, HALL_M_MAX, DEFAULT_HALL_M = 0, 4, 0
HALL_FREI_OPTIONEN, DEFAULT_HALL_FREI = (2, 3), 3
ORDNUNG_MIN, ORDNUNG_MAX, DEFAULT_ORDNUNG = 6, 15, 10
LUECKE_MIN, LUECKE_MAX, DEFAULT_LUECKE = 35, 65, 58   # Lückenanteil in Prozent

SWEEP_DATEI = "ald_sweep_vorgerechnet.json"
SEED_ANZEIGE_LIMIT = 20                                # der vorgerechnete Sweep nutzt die Seeds 0 bis 19

# Vormessung der Hall-Verletzung (Rohdatei out_cp_v10_hall.txt der Planung, Mini-CP der Phase 0; nur zur Kontrolle, nicht als Ersatz der Live-Rechnung).
# Schlüssel (k, m): Knoten der Stufe A bei freien Variablen mit drei Werten; None = Abbruch am Budget 50 000.
VORMESSUNG_HALL_A = {
    (4, 0): 41, (5, 0): 206, (6, 0): 1237, (7, 0): 8660, (8, 0): None, (9, 0): None,
    (4, 3): 1120, (5, 3): 5575, (6, 3): 33412, (7, 3): None, (8, 3): None, (9, 3): None,
}
VORMESSUNG_BUDGET = 50000

COLOR_IN = "#cfe3df"        # Wert in der Domäne
COLOR_FIXED = "#2F6B65"     # Variable ist festgelegt
COLOR_GONE = "#d9534f"      # Wert in diesem Schritt gestrichen
COLOR_OUT = "#f0f0f0"       # Wert nie in der Domäne
STUFEN_FARBEN = {"A": "#9aa0a6", "B": "#4c78a8", "C": "#2F6B65"}

PRESETS = {
    "Handbeispiel H2 (Löcher)": {},
    "Handbeispiel H3 (Rotationsplan 4 × 4)": {"beispiel": BEISPIEL_H3},
    "Hall-Verletzung k = 5": {"hall_k": 5},
    "Rotationsplan 12": {"ordnung": 12},
}
PRESET_HELP = {
    "Handbeispiel H2 (Löcher)": "Reiter „Eine Gruppe von Hand“: vier Variablen mit Löchern in den Domänen. Stufe A streicht nichts, B setzt x4 = 4, C setzt zusätzlich x3 = 2.",
    "Handbeispiel H3 (Rotationsplan 4 × 4)": "Reiter „Eine Gruppe von Hand“: 4 × 4-Rotationsplan mit vier Vorbelegungen. Nach der Wurzel sind 4 (A), 6 (B) und 8 (C) Zellen festgelegt.",
    "Hall-Verletzung k = 5": "Reiter „Hall-Verletzung wächst“: sechs Variablen auf fünf Werte. Die paarweise Suche braucht 206 Knoten, Bounds und Régin einen.",
    "Rotationsplan 12": "Reiter „Rotationsplan mit Lücken“: Ordnung 12 mit 58 % Lücken, Zufalls-Seed 0, eine Einzelinstanz und der vorgerechnete Sweep.",
}
