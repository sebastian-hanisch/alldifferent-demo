"""Jede Zahl der README (und der Texte der App) wird hier nachgerechnet. Zahl -> Test steht in der Tabelle „Befunde“ der README.

Zwei Arten von Zahlen: (1) exakte Zählungen der deterministischen Suche (Hall-Instanzen, Handbeispiele; auf jeder Plattform gleich, weil die Suche ganzzahlig
ist und kein Zufall vorkommt); (2) der vorgerechnete Sweep `ald_sweep_vorgerechnet.json` (Messung dieses Repos mit `tools/messung_sweep.py`,
Seeds 0 bis 19 des SplitMix64-Erzeugers); eine Stichprobe der Zellen wird hier live nachgerechnet, die übrigen nur aus der Datei gelesen.
Sekunden werden nirgends geprüft."""

import json
import statistics

import pytest

import ald_constants as C
import ald_evaluation as E
import ald_scenario as S
import ald_search as Q
from conftest import lauf


def _hall(m, frei=3, k_max=9, budget=50000):
    return {z["k"]: z for z in E.hall_zeilen(k_max, m, frei, budget)}


# ---------------------------------------------------------------- Hall-Verletzung
def test_claim_hall_ohne_freie_variablen():
    """k = 3 bis 7: A 10 / 41 / 206 / 1 237 / 8 660 Knoten; ab k = 8 Abbruch am Budget 50 000; B und C immer 1 Knoten."""
    z = _hall(0)
    assert [z[k]["A"].knoten for k in range(3, 8)] == [10, 41, 206, 1237, 8660]
    assert not any(z[k]["A"].abgebrochen for k in range(3, 8))
    assert all(z[k]["A"].abgebrochen and z[k]["A"].knoten == 50000 for k in (8, 9))
    assert all(z[k][s].knoten == 1 and z[k][s].fehlschlaege == 1 for k in z for s in "BC")
    # Faktor je zusätzlichem Wert: 41 -> 206 -> 1 237 -> 8 660 wächst um 5,0 / 6,0 / 7,0
    f = [z[k + 1]["A"].knoten / z[k]["A"].knoten for k in range(4, 7)]
    assert [round(x, 1) for x in f] == [5.0, 6.0, 7.0]


def test_claim_hall_mit_freien_variablen_vervielfacht_den_schaden():
    """Drei freie Variablen mit drei Werten: k = 3 bis 6: 283 / 1 120 / 5 575 / 33 412; ab k = 7 Abbruch; 1 120 gegen 41 ist das 27,3-Fache (27 = 3^3 Belegungen)."""
    z = _hall(3)
    assert [z[k]["A"].knoten for k in range(3, 7)] == [283, 1120, 5575, 33412]
    assert z[7]["A"].abgebrochen and all(z[k][s].knoten == 1 for k in z for s in "BC")
    assert round(1120 / _hall(0, k_max=4)[4]["A"].knoten, 1) == 27.3
    assert 3 ** 3 == 27


def test_claim_vormessung_der_planung_wird_reproduziert():
    """Die Knotenzahlen der Vormessung (out_cp_v10_hall.txt) stehen als Vergleichsspalte in der App; sie müssen gleich sein, wo kein Abbruch vorliegt."""
    for (k, m), erwartet in C.VORMESSUNG_HALL_A.items():
        z = E.hall_zeilen(k, m, 3, 50000)[-1]
        if erwartet is None:
            assert z["A"].abgebrochen
        else:
            assert z["A"].knoten == erwartet, (k, m)


def test_claim_hall_kosten_je_aufruf_und_gesamt():
    """Auf der Hall-Instanz k = 7 (ohne freie Variablen): A 623 520 Grundoperationen in 8 660 Aufrufen (72 je Aufruf), C 148 in einem Aufruf."""
    z = _hall(0, k_max=7)[7]
    assert (z["A"].ops, z["A"].aufrufe, round(z["A"].ops_je_aufruf)) == (623520, 8660, 72)
    assert (z["C"].ops, z["C"].aufrufe) == (148, 1)
    assert (z["B"].ops, z["B"].aufrufe) == (40, 1)
    assert [round(_hall(0, k_max=7)[k]["A"].ops_je_aufruf) for k in (4, 5, 6, 7)] == [30, 42, 56, 72]


# ---------------------------------------------------------------- Handbeispiele
def test_claim_h1_h2_h3():
    assert [lauf(S.h1_hall(), s).knoten for s in "ABC"] == [175, 1, 1] and lauf(S.h1_hall(), "A").fehlschlaege == 96
    tab = E.wurzel_tabelle(S.h2_loecher())
    assert [(tab[s].festgelegt, tab[s].gestrichen) for s in "ABC"] == [(0, 0), (1, 2), (2, 4)]
    tab = E.wurzel_tabelle(S.h3_rotationsplan())
    assert [tab[s].festgelegt for s in "ABC"] == [4, 6, 8]


def test_claim_presets_und_texte_der_app_nennen_nur_gemessene_zahlen():
    assert E.verdict_kern({s: E.messung(lauf(S.h1_hall(), s)) for s in "ABC"})[1].count("175 Knoten (96 Fehlschläge)") == 1
    assert lauf(S.hall_instanz(5, 0), "A").knoten == 206                          # Preset „Hall-Verletzung k = 5“
    assert lauf(S.hall_instanz(6, 0), "A").knoten == 1237                         # Einleitung: sieben Variablen auf sechs Werte
    assert "206 Knoten" in C.PRESET_HELP["Hall-Verletzung k = 5"] and "4 (A), 6 (B) und 8 (C)" in C.PRESET_HELP["Handbeispiel H3 (Rotationsplan 4 × 4)"]
    assert "58 %" in C.PRESET_HELP["Rotationsplan 12"] and C.PRESETS["Rotationsplan 12"] == {"ordnung": 12}
    assert C.DEFAULT_LUECKE == 58 and C.DEFAULT_SEED == 0
