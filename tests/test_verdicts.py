"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zahlen, nicht Seeds."""

import ald_evaluation as ev
from ald_evaluation import Messung


def M(knoten, aufrufe=10, ops=100, abgebrochen=False, fehl=0, fest=None):
    return Messung(knoten, fehl, aufrufe, ops, abgebrochen, fest)


# ---------------------------------------------------------------- Kernfrage und Hall
def test_verdict_kern_nennt_alle_drei_knotenzahlen():
    art, text = ev.verdict_kern({"A": M(175, fehl=96), "B": M(1), "C": M(1)})
    assert art == "success"
    assert "nach 175 Knoten (96 Fehlschläge)" in text and "Bounds nach 1 und Régin nach 1" in text


def test_verdict_kern_ohne_unterschied_sagt_genuegt():
    art, text = ev.verdict_kern({"A": M(1), "B": M(1), "C": M(1)})
    assert art == "info" and "genügt die paarweise Prüfung" in text


def test_verdict_hall_wachstumsfaktor_und_budget():
    zeilen = [{"k": 4, "A": M(41), "B": M(1), "C": M(1)}, {"k": 5, "A": M(206), "B": M(1), "C": M(1)}]
    art, text = ev.verdict_hall(zeilen, 0)
    assert art == "success" and "Bei k = 5 (6 Variablen auf 5 Werte, ohne freie Variablen)" in text
    assert "nach 206 Knoten" in text and "wächst A auf das 5,0-fache" in text            # 206 / 41 = 5,02
    zeilen.append({"k": 8, "A": M(50000, abgebrochen=True), "B": M(1), "C": M(1)})
    art, text = ev.verdict_hall(zeilen, 3)
    assert "mit 3 freien Variablen" in text and "mindestens 50 000 (Budget erreicht)" in text
    assert "wächst A auf das 5,0-fache" in text                                           # die abgebrochene Zeile zählt für den Faktor nicht


def test_verdict_hall_ohne_unterschied():
    art, text = ev.verdict_hall([{"k": 3, "A": M(1), "B": M(1), "C": M(1)}], 0)
    assert art == "info" and "genügt die paarweise Prüfung" in text and "wächst" not in text


# ---------------------------------------------------------------- Wurzel (Reiter 1)
def _w(ok, fest, gestr):
    return ev.Wurzel("A", ok, fest, gestr, 1, 1, (), ())


def test_verdict_wurzel_drei_verschiedene_staerken():
    art, text = ev.verdict_wurzel({"A": _w(True, 4, 0), "B": _w(True, 6, 5), "C": _w(True, 8, 9)}, 16)
    assert art == "success" and "A paarweise: 4 von 16 Variablen festgelegt, 0 Werte gestrichen" in text and "C Régin: 8 von 16" in text


def test_verdict_wurzel_widerspruch_nur_in_b_und_c():
    art, text = ev.verdict_wurzel({"A": _w(True, 0, 0), "B": _w(False, 0, 0), "C": _w(False, 0, 0)}, 4)
    assert art == "success" and "Widerspruch an der Wurzel" in text and "merkt den Widerspruch nicht" in text


def test_verdict_wurzel_gleich_sagt_genuegt():
    art, text = ev.verdict_wurzel({"A": _w(True, 2, 2), "B": _w(True, 2, 2), "C": _w(True, 2, 2)}, 5)
    assert art == "info" and "genügt die paarweise Prüfung" in text


# ---------------------------------------------------------------- Einzelinstanz
def test_verdict_einzel_nennt_knoten_fehlschlaege_und_festgelegte_zellen():
    m = {"A": M(92, fehl=40, fest=40), "B": M(53, fehl=21, fest=44), "C": M(11, fehl=0, fest=50)}
    art, text = ev.verdict_einzel(m, 10, 58)
    assert art == "success"
    assert "Ordnung 10 mit 58 % Lücken: A braucht 92 Knoten (40 Fehlschläge), B 53 (21), C 11 (0)" in text
    assert "40 (A), 44 (B) und 50 (C) von 100 Zellen" in text


def test_verdict_einzel_gleiche_knoten_oder_abbruch():
    m = {"A": M(14, fest=1), "B": M(14, fest=1), "C": M(14, fest=1)}
    art, text = ev.verdict_einzel(m, 10, 58)
    assert art == "info" and "hier genügt die paarweise Prüfung" in text
    m["A"] = M(20000, abgebrochen=True, fest=1)
    art, text = ev.verdict_einzel(m, 10, 58)
    assert art == "success" and "mindestens 20 000 (Budget erreicht)" in text


# ---------------------------------------------------------------- Verteilung (Sweep)
def _v(median, p90, maxi, abbr, n=20, budget=20000):
    return {"n": n, "median": median, "p90": p90, "max": maxi, "abbrueche": abbr, "budget": budget}


def test_perzentil_nach_naechstem_rang_von_hand():
    assert ev.perzentil(list(range(1, 11)), 0.9) == 9              # zehn Werte: Rang ceil(0,9 * 10) = 9
    assert ev.perzentil([5, 1, 3], 0.9) == 5 and ev.perzentil([7], 0.9) == 7
    assert ev.perzentil(list(range(1, 21)), 0.9) == 18             # zwanzig Werte: Rang 18


def test_verteilung_zaehlt_median_max_und_abbrueche():
    zeilen = [{"knoten": k, "fehlschlaege": 0, "aufrufe": 10, "ops_dom": 60, "ops_kanten": 40, "abgebrochen": a, "festgelegt_wurzel": 3}
              for k, a in ((10, False), (20, False), (30, False), (20000, True))]
    v = ev.verteilung(zeilen, 20000)
    assert v["median"] == 25 and v["max"] == 20000 and v["abbrueche"] == 1 and v["n"] == 4 and v["p90"] == 20000
    assert v["ops_je_aufruf_median"] == 10 and v["ops_median"] == 100


def test_verdict_verteilung_schwanz_nicht_median():
    v = {"A": _v(18.5, 200, 816, 0), "B": _v(15, 100, 211, 0), "C": _v(13.5, 17, 19, 0)}
    art, text = ev.verdict_verteilung(v, 10, 58)
    assert art == "success"
    assert "Median 18,5 Knoten bei A gegen 13,5 bei C (Verhältnis 1,4)" in text and "Maximum 816 gegen 19" in text      # 18,5 / 13,5 = 1,37
    assert text.endswith("Der Gewinn liegt im Schwanz, nicht im Median.")
    v["A"] = _v(34, 20000, 20000, 3)
    art, text = ev.verdict_verteilung(v, 12, 58)
    assert "(A: 3, B: 0, C: 0)" in text and "Median 34 Knoten" in text


def test_verdict_verteilung_median_doppelt():
    v = {"A": _v(100, 300, 400, 0), "C": _v(40, 50, 60, 0)}
    art, text = ev.verdict_verteilung(v, 15, 50)
    assert art == "success" and "Schon im Median braucht A mindestens doppelt so viele Knoten wie C." in text and "(A: 0, C: 0)" in text


def test_verdict_verteilung_genuegt_ohne_unterschied():
    v = {"A": _v(10, 12, 13, 0), "C": _v(9, 11, 12, 0)}
    art, text = ev.verdict_verteilung(v, 10, 50)
    assert art == "info" and "Hier genügt die paarweise Prüfung: Median-Verhältnis unter 2, Maximum-Verhältnis unter 5" in text
    # Schwellen: Maximum-Verhältnis genau 5 zählt als Schwanz, knapp darunter nicht
    assert ev.verdict_verteilung({"A": _v(10, 12, 50, 0), "C": _v(9, 10, 10, 0)}, 10, 50)[0] == "success"
    assert ev.verdict_verteilung({"A": _v(10, 12, 49, 0), "C": _v(9, 10, 10, 0)}, 10, 50)[0] == "info"


# ---------------------------------------------------------------- Kosten
def test_verdict_kosten_gesamt_gegen_je_aufruf():
    """A: 100 Knoten, 200 Aufrufe, 2 000 Operationen (10 je Aufruf); C: 20 Knoten, 40 Aufrufe, 1 000 Operationen (25 je Aufruf).
    Von Hand: 100/20 = 5 mal weniger Knoten; je Aufruf 25/10 = 2,5-mal so viele; gesamt 2000/1000 = 2 mal weniger."""
    m = {"A": M(100, 200, 2000), "B": M(60, 120, 6000), "C": M(20, 40, 1000)}
    art, text = ev.verdict_kosten(m)
    assert art == "success"
    assert "5,0-mal weniger Knoten" in text and "2,5-mal so viele Grundoperationen (25 gegen 10)" in text
    assert "unterm Strich braucht Régin 2,0-mal weniger Grundoperationen" in text
    assert "Insgesamt A 2 000, C 1 000, zum Vergleich B 6 000 (50 je Aufruf)" in text


def test_verdict_kosten_regin_unterm_strich_teurer_ist_eine_warnung():
    m = {"A": M(10, 20, 400), "C": M(8, 16, 1600)}       # weniger Knoten, aber 4-mal so viele Operationen gesamt
    art, text = ev.verdict_kosten(m)
    assert art == "warning" and "unterm Strich braucht Régin 4,0-mal mehr Grundoperationen" in text and "zum Vergleich B" not in text


def test_verdict_kosten_gleichstand_und_abbruch_und_fehlende_werte():
    assert ev.verdict_kosten({"A": M(10, 10, 100), "C": M(10, 10, 100)})[0] == "info"      # Verhältnis 1: unter der Schwelle 1,25
    assert ev.verdict_kosten({"A": M(10, 10, 125), "C": M(10, 10, 100)})[0] == "success"   # genau 1,25 zählt
    art, text = ev.verdict_kosten({"A": M(50000, 70000, 5_000_000, abgebrochen=True), "C": M(1, 1, 50)})
    assert "mindestens 50 000,0-mal weniger Knoten" in text
    assert ev.verdict_kosten({"A": M(0, 0, 0), "C": M(1, 1, 5)})[0] == "info"
