"""Zahlen der README aus dem vorgerechneten Sweep `ald_sweep_vorgerechnet.json` (Messung dieses Repos mit `tools/messung_sweep.py`, Seeds 0 bis 19 des SplitMix64-Erzeugers,
Knotenbudget 20 000). Eine Stichprobe der Zellen wird hier live nachgerechnet (Lauf für Lauf gleich), die übrigen werden aus der Datei gelesen und gezählt.
Sekunden werden nirgends geprüft."""

import pytest

import ald_evaluation as E
import ald_scenario as S
import ald_search as Q


@pytest.fixture(scope="module")
def sweep():
    return E.lade_sweep()


def _v(sweep, o, p):
    return E.zellen_verteilung(sweep, o, p)


ZELLEN_ALLE = [(o, p) for o in (10, 12, 14, 15) for p in (50, 55, 58, 62)] + [(15, 35), (15, 40), (15, 45)]
NUR_AC = ((15, 35), (15, 40), (15, 45))


def test_claim_sweep_raster_seeds_budget_und_gegenprobe(sweep):
    """19 Zellen (Ordnung 10, 12, 14, 15 mit 50, 55, 58, 62 % Lücken sowie Ordnung 15 mit 35, 40, 45 %; die drei Zusatzzellen nur mit A und C), 20 Seeds, Budget 20 000."""
    meta = sweep["meta"]
    assert meta["seeds"] == list(range(20)) and meta["knotenbudget"] == 20000 and meta["nur_erfuellbar"] is True
    assert meta["gegenprobe"] == "CP-SAT und Lösungsprüfer, Abweichungen: 0"
    assert [(z["ordnung"], z["luecken"]) for z in sweep["zellen"]] == ZELLEN_ALLE
    for z in sweep["zellen"]:
        erwartet = "AC" if (z["ordnung"], z["luecken"]) in NUR_AC else "ABC"
        assert "".join(z["stufen"]) == erwartet
        assert all([r["seed"] for r in rows] == list(range(20)) for rows in z["stufen"].values())


def test_claim_sweep_stichprobe_live_nachgerechnet(sweep):
    """Ordnung 10 (alle vier Lückenanteile, alle drei Stärken) und Ordnung 15 mit 35 und 40 % (A und C) werden live neu gerechnet und müssen Lauf für Lauf gleich sein."""
    zellen = [(10, p, "ABC") for p in (50, 55, 58, 62)] + [(15, 35, "AC"), (15, 40, "AC")]
    for o, p, stufen in zellen:
        z = E.sweep_zelle(sweep, o, p)
        for seed in range(20):
            inst, _ = S.rotationsplan_instanz(o, p, seed)
            for s in stufen:
                r = Q.loese(inst.dom_liste(), inst.gruppen, s, budget=20000)
                ref = z["stufen"][s][seed]
                assert (r.knoten, r.fehlschlaege, r.aufrufe, r.ops_dom, r.ops_kanten, r.antwort == "abgebrochen", r.festgelegt_wurzel) == (
                    ref["knoten"], ref["fehlschlaege"], ref["aufrufe"], ref["ops_dom"], ref["ops_kanten"], ref["abgebrochen"], ref["festgelegt_wurzel"]), (o, p, s, seed)
                assert r.antwort != "unloesbar"                                    # erfüllbar nach Konstruktion


def test_claim_ordnung_10_58_prozent(sweep):
    """Ordnung 10, 58 % Lücken, 20 Seeds: Median 21 (A), 15,5 (B), 14 (C) Knoten; 90-Prozent-Rang 69 / 26 / 17; Maximum 519 / 187 / 19; kein Abbruch."""
    v = _v(sweep, 10, 58)
    assert [v[s]["median"] for s in "ABC"] == [21, 15.5, 14]
    assert [v[s]["p90"] for s in "ABC"] == [69, 26, 17]
    assert [v[s]["max"] for s in "ABC"] == [519, 187, 19]
    assert [v[s]["abbrueche"] for s in "ABC"] == [0, 0, 0]
    assert round(v["A"]["median"] / v["C"]["median"], 1) == 1.5


def test_claim_regin_bricht_nie_ab_und_braucht_hoechstens_76_knoten(sweep):
    """In allen 19 Zellen (380 Läufe): Régin nie am Budget, Maximum 76 Knoten; in den 42 Läufen, in denen A am Budget abbricht, löst Régin mit 13 bis 74 Knoten."""
    assert sum(_v(sweep, o, p)["C"]["abbrueche"] for o, p in ZELLEN_ALLE) == 0
    assert max(_v(sweep, o, p)["C"]["max"] for o, p in ZELLEN_ALLE) == 76
    knoten_c = [c["knoten"] for z in sweep["zellen"] for a, c in zip(z["stufen"]["A"], z["stufen"]["C"]) if a["abgebrochen"]]
    assert len(knoten_c) == 42 and min(knoten_c) == 13 and max(knoten_c) == 74


def test_claim_abbrueche_von_a_und_b_je_zelle(sweep):
    """Abbrüche je Zelle (Lücken 50 / 55 / 58 / 62 %): A Ordnung 10: 0 / 0 / 0 / 1, 12: 0 / 0 / 1 / 4, 14: 4 / 8 / 3 / 2, 15: 4 / 3 / 7 / 5; B Ordnung 12: 0 / 0 / 1 / 2, 14: 1 / 1 / 3 / 1,
    15: 1 / 1 / 5 / 0; insgesamt A 42 von 380, B 16 von 320."""
    def abbr(s, o):
        return [_v(sweep, o, p)[s]["abbrueche"] for p in (50, 55, 58, 62)]

    assert [abbr("A", o) for o in (10, 12, 14, 15)] == [[0, 0, 0, 1], [0, 0, 1, 4], [4, 8, 3, 2], [4, 3, 7, 5]]
    assert [abbr("B", o) for o in (10, 12, 14, 15)] == [[0, 0, 0, 0], [0, 0, 1, 2], [1, 1, 3, 1], [1, 1, 5, 0]]
    assert sum(_v(sweep, o, p)["A"]["abbrueche"] for o, p in ZELLEN_ALLE) == 42
    assert sum(_v(sweep, o, p)["B"]["abbrueche"] for o, p in ZELLEN_ALLE if (o, p) not in NUR_AC) == 16
    assert sum(len(z["stufen"]["B"]) for z in sweep["zellen"] if "B" in z["stufen"]) == 320


def test_claim_median_verhaeltnis_waechst_mit_der_ordnung(sweep):
    """Median A durch Median C bei 58 % Lücken: 1,5 (Ordnung 10), 1,4 (12), 1,7 (14), 73,9 (15); bei 50 % Lücken 1,8 / 2,3 / 52,5 / 44,5."""
    def q(o, p):
        v = _v(sweep, o, p)
        return round(v["A"]["median"] / v["C"]["median"], 1)

    assert [q(o, 58) for o in (10, 12, 14, 15)] == [1.5, 1.4, 1.7, 73.9]
    assert [q(o, 50) for o in (10, 12, 14, 15)] == [1.8, 2.3, 52.5, 44.5]
    assert _v(sweep, 15, 58)["A"]["median"] == 3844.5 and _v(sweep, 15, 58)["C"]["median"] == 52
    # Schwelle 2 je Zelle: Ordnung 10 überall darunter; 50 und 55 % schon bei Ordnung 12 darüber, 58 und 62 % erst bei Ordnung 15
    q2 = lambda o, p: round(_v(sweep, o, p)["A"]["median"] / _v(sweep, o, p)["C"]["median"], 2)
    assert [q2(10, p) for p in (50, 55, 58, 62)] == [1.78, 1.55, 1.5, 1.42]
    assert [q2(12, p) for p in (50, 55)] == [2.33, 2.12] and [q2(14, p) for p in (58, 62)] == [1.68, 1.53]
    assert q2(12, 62) < 2 and round(q2(15, 62), 1) == 3.5


def test_claim_c_gegen_a_knoten_je_lauf(sweep):
    """Über alle 380 Läufe braucht C in 335 weniger, in 37 gleich viele und in 8 mehr Knoten als A."""
    paare = [(a["knoten"], c["knoten"]) for z in sweep["zellen"] for a, c in zip(z["stufen"]["A"], z["stufen"]["C"])]
    assert len(paare) == 380
    assert (sum(c < a for a, c in paare), sum(c == a for a, c in paare), sum(c > a for a, c in paare)) == (335, 37, 8)


def test_claim_fehlschlaege_von_c(sweep):
    """C hat in jeder Zelle den Median 0 Fehlschläge, aber in 68 von 380 Läufen mindestens einen (höchstens 6)."""
    assert all(_v(sweep, o, p)["C"]["fehlschlaege_median"] == 0 for o, p in ZELLEN_ALLE)
    laeufe = [r["fehlschlaege"] for z in sweep["zellen"] for r in z["stufen"]["C"]]
    assert len(laeufe) == 380 and sum(1 for f in laeufe if f > 0) == 68 and max(laeufe) == 6


def test_claim_a_fehlschlaege_ordnung_15(sweep):
    """Median der Fehlschläge von A bei Ordnung 15 und 35 / 40 / 45 / 50 / 55 / 58 / 62 % Lücken: 0 / 1 / 11,5 / 432 / 147 / 1 895 / 86,5."""
    assert [_v(sweep, 15, p)["A"]["fehlschlaege_median"] for p in (35, 40, 45, 50, 55, 58, 62)] == [0, 1, 11.5, 432, 147, 1895, 86.5]


def test_claim_kosten_je_aufruf_und_gesamt(sweep):
    """Grundoperationen je Aufruf (Median je Zelle): A 82 bis 238, B 467 bis 1 798, C 115 bis 259; C das 0,87- bis 1,63-Fache von A, B das 5,7- bis 8,9-Fache von A.
    Gesamtkosten (Median der Summe): A durch C bei 58 % Lücken 0,87 (Ordnung 10), 0,80 (12), 1,12 (14), 39,1 (15); in 5 von 19 Zellen kostet C im Median mehr als A."""
    je = {s: [_v(sweep, o, p)[s]["ops_je_aufruf_median"] for o, p in ZELLEN_ALLE if s in _v(sweep, o, p)] for s in "ABC"}
    assert (round(min(je["A"])), round(max(je["A"]))) == (82, 238)
    assert (round(min(je["B"])), round(max(je["B"]))) == (467, 1798)
    assert (round(min(je["C"])), round(max(je["C"]))) == (115, 259)
    c_a = [_v(sweep, o, p)["C"]["ops_je_aufruf_median"] / _v(sweep, o, p)["A"]["ops_je_aufruf_median"] for o, p in ZELLEN_ALLE]
    assert (round(min(c_a), 2), round(max(c_a), 2)) == (0.87, 1.63)
    b_a = [_v(sweep, o, p)["B"]["ops_je_aufruf_median"] / _v(sweep, o, p)["A"]["ops_je_aufruf_median"] for o, p in ZELLEN_ALLE if (o, p) not in NUR_AC]
    assert (round(min(b_a), 1), round(max(b_a), 1)) == (5.7, 8.9)
    gesamt = {(o, p): _v(sweep, o, p)["A"]["ops_median"] / _v(sweep, o, p)["C"]["ops_median"] for o, p in ZELLEN_ALLE}
    assert [round(gesamt[(o, 58)], 2) for o in (10, 12, 14, 15)] == [0.87, 0.8, 1.12, 39.1]
    assert sorted(k for k, g in gesamt.items() if g < 1) == [(10, 55), (10, 58), (10, 62), (12, 58), (14, 62)]
    assert all(_v(sweep, o, p)["B"]["ops_median"] > _v(sweep, o, p)["C"]["ops_median"] for o, p in ZELLEN_ALLE if (o, p) not in NUR_AC)


def test_claim_festgelegte_zellen_nach_der_wurzel(sweep):
    """Ordnung 10, 58 % Lücken (42 vorbelegt): im Median 44,5 (A), 44,5 (B), 46,5 (C) festgelegte Zellen; C legt in 281 von 380 Läufen mehr fest als A, B in 140 von 320."""
    v = _v(sweep, 10, 58)
    assert [v[s]["festgelegt_median"] for s in "ABC"] == [44.5, 44.5, 46.5]
    c_mehr = b_mehr = b_laeufe = 0
    for z in sweep["zellen"]:
        for i, a in enumerate(z["stufen"]["A"]):
            c_mehr += z["stufen"]["C"][i]["festgelegt_wurzel"] > a["festgelegt_wurzel"]
            if "B" in z["stufen"]:
                b_laeufe += 1
                b_mehr += z["stufen"]["B"][i]["festgelegt_wurzel"] > a["festgelegt_wurzel"]
    assert (c_mehr, b_mehr, b_laeufe) == (281, 140, 320)


def test_claim_teilmengenordnung_der_wurzel_je_lauf(sweep):
    """C legt nach der Wurzel nie weniger Zellen fest als B und B nie weniger als A (je Lauf gezählt)."""
    for z in sweep["zellen"]:
        for i, a in enumerate(z["stufen"]["A"]):
            c = z["stufen"]["C"][i]["festgelegt_wurzel"]
            assert c >= a["festgelegt_wurzel"]
            if "B" in z["stufen"]:
                assert c >= z["stufen"]["B"][i]["festgelegt_wurzel"] >= a["festgelegt_wurzel"]


def test_claim_tabelle_58_prozent_alle_ordnungen(sweep):
    """README-Tabelle bei 58 % Lücken: Median / 90-Prozent-Rang / Maximum der Knoten je Stärke (A, B, C) und Abbrüche."""
    erwartet = {
        10: ([21, 15.5, 14], [69, 26, 17], [519, 187, 19], [0, 0, 0]),
        12: ([38.5, 31.5, 27.5], [5727, 223, 34], [20000, 20000, 36], [1, 1, 0]),
        14: ([70.5, 50, 42], [20000, 20000, 44], [20000, 20000, 47], [3, 3, 0]),
        15: ([3844.5, 63.5, 52], [20000, 20000, 58], [20000, 20000, 59], [7, 5, 0]),
    }
    for o, (med, p90, mx, ab) in erwartet.items():
        v = _v(sweep, o, 58)
        assert [v[s]["median"] for s in "ABC"] == med, o
        assert [v[s]["p90"] for s in "ABC"] == p90, o
        assert [v[s]["max"] for s in "ABC"] == mx, o
        assert [v[s]["abbrueche"] for s in "ABC"] == ab, o


def test_claim_aufrufe_ordnung_10_58_prozent(sweep):
    """Propagationsaufrufe im Median bei Ordnung 10 und 58 % Lücken: 204,5 (A) gegen 158 (C)."""
    v = _v(sweep, 10, 58)
    assert v["A"]["aufrufe_median"] == 204.5 and v["C"]["aufrufe_median"] == 158
