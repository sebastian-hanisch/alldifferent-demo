"""Kern gegen Handrechnung (DEMO-PLAYBOOK §1b): jede Einheit auf einer Mini-Instanz, deren Ergebnis von Hand gerechnet ist (Plan Stück 10, H1 bis H3).

Nichts hier schreibt Werte des Codes ab: Die Erwartungen stehen als Rechnung oder als Mengenargument im Test."""

import pytest

import ald_algorithm as A
import ald_scenario as S
import ald_search as Q
from conftest import lauf, wurzel


# ---------------------------------------------------------------- H1: Hall-Verletzung in acht Variablen
def test_h1_knoten_von_hand():
    """Von Hand: vier freie Variablen mit zwei Werten kommen zuerst: 1 + 2 + 4 + 8 = 15 Knoten oberhalb der 16 Blätter. Unter jedem Blatt sucht Stufe A in der
    a-Gruppe: Wurzel, 3 Werte für a1, unter jedem 2 gescheiterte Werte für a2 = 10 Knoten. Stufe A: 15 + 16 * 10 = 175 Knoten, 16 * 6 = 96 Fehlschläge."""
    a = lauf(S.h1_hall(), "A")
    assert a.knoten == 15 + 16 * 10 == 175
    assert a.fehlschlaege == 16 * 3 * 2             # je Blatt: 3 Werte für a1, darunter je 2 gescheiterte Werte für a2 = 6 Fehlschläge
    assert a.loesungen == 0 and a.antwort == "unloesbar"
    for stufe in "BC":
        r = lauf(S.h1_hall(), stufe)
        assert (r.knoten, r.fehlschlaege, r.antwort) == (1, 1, "unloesbar")  # Wurzel: 4 Variablen im Intervall [1, 3] mit 3 Werten; Matching hat Größe 3 < 4


def test_h1_gruppe_allein_und_vergleich_mit_der_vormessung():
    assert [lauf(S.hall_instanz(3, 0), s).knoten for s in "ABC"] == [10, 1, 1]
    assert lauf(S.hall_instanz(4, 0), "A").knoten == 41     # Vormessung out_cp_v10_hall.txt, k = 4
    assert lauf(S.hall_instanz(5, 0), "A").knoten == 206    # k = 5
    assert lauf(S.hall_instanz(4, 3), "A").knoten == 1120   # k = 4 mit drei freien Variablen (1120 = 27 * 41 + 13)


# ---------------------------------------------------------------- H2: Löcher in den Domänen
def test_h2_wurzel_pro_stufe(h2):
    assert wurzel(h2, "A") == [[1, 3], [1, 3], [1, 2, 3], [2, 3, 4]]        # keine Domäne einelementig: A streicht nichts
    # Bounds: Intervall [1, 3] enthält x1, x2, x3 (3 Variablen, 3 Werte), also springt die untere Schranke von x4 auf 4; x3 behält die Lücke {2}
    assert wurzel(h2, "B") == [[1, 3], [1, 3], [1, 2, 3], [4]]
    # Régin: x1, x2 teilen sich {1, 3}, also bleibt für x3 nur 2 und für x4 nur 4
    assert wurzel(h2, "C") == [[1, 3], [1, 3], [2], [4]]


def test_h2_regin_matching_und_komponenten(h2):
    dom = h2.dom_liste()
    z = A.Zaehler()
    a = A.regin_analyse(dom, [0, 1, 2, 3], z)
    assert a["ok"] and a["groesse"] == 4
    # Komponenten: {x1, x2, 1, 3} (Kreis x1 -> 1 -> x2 -> 3 -> x1), alle anderen Knoten einzeln
    komp = a["komp"]
    assert komp[("v", 0)] == komp[("v", 1)] == komp[("w", 1)] == komp[("w", 3)]
    einzeln = [komp[("v", 2)], komp[("v", 3)], komp[("w", 2)], komp[("w", 4)]]
    assert len(set(einzeln)) == 4 and komp[("v", 0)] not in einzeln
    assert sorted(a["streiche"]) == [(2, 1), (2, 3), (3, 2), (3, 3)]     # x3-1, x3-3, x4-2, x4-3 (Plan)


def test_regin_zweites_beispiel_von_hand():
    """x1 {1,2}, x2 {1,2}, x3 {1,2,3}, x4 {3,4}: x1, x2 teilen sich {1, 2}, also x3 = 3, x4 = 4."""
    inst = S.aus_domaenen([{1, 2}, {1, 2}, {1, 2, 3}, {3, 4}])
    assert wurzel(inst, "C") == [[1, 2], [1, 2], [3], [4]]


def test_beschreibung_h2_stufe_c_nennt_die_hall_menge(h2):
    ok, dom, spur, z = Q.wurzel_propagation(h2.dom_liste(), h2.gruppen, "C", spur=True)
    assert ok and len(spur) == 4
    satz = A.beschreibe(spur[0], lambda i: h2.namen[i])
    assert "x1, x2" in satz and "{1, 3}" in satz and "fällt 1 aus x3" in satz


# ---------------------------------------------------------------- H3: Rotationsplan 4 x 4
def test_h3_festgelegte_zellen_pro_stufe(h3):
    """Nach der Wurzel: A 4 (nur die Vorbelegungen), B 6 (zusätzlich (1,2) = 4 und (3,0) = 4), C 8 (zusätzlich (0,1) = 2 und (2,3) = 2)."""
    fest = {s: [i for i, d in enumerate(wurzel(h3, s)) if len(d) == 1] for s in "ABC"}
    assert [len(fest[s]) for s in "ABC"] == [4, 6, 8]
    zelle = lambda r, c: 4 * r + c
    assert set(fest["B"]) - set(fest["A"]) == {zelle(1, 2), zelle(3, 0)}
    assert set(fest["C"]) - set(fest["B"]) == {zelle(0, 1), zelle(2, 3)}
    d = wurzel(h3, "C")
    assert d[zelle(0, 1)] == [2] and d[zelle(2, 3)] == [2] and d[zelle(1, 2)] == [4] and d[zelle(3, 0)] == [4]


def test_h3_suche_drei_knoten_vier_loesungen(h3):
    for s in "ABC":
        r = lauf(h3, s)
        assert (r.knoten, r.fehlschlaege) == (3, 0)
        assert r.loesung == (1, 2, 3, 4, 2, 1, 4, 3, 3, 4, 1, 2, 4, 3, 2, 1)
        assert lauf(h3, s, alle=True).loesungen == 4


# ---------------------------------------------------------------- Einheiten
def test_paarweise_kaskade():
    """x1 = {1}, x2 {1, 2}, x3 {2, 3}: 1 fällt aus x2, dann ist x2 = {2}, und 2 fällt aus x3: x3 = {3}."""
    dom = [{1}, {1, 2}, {2, 3}]
    ch = A.prop_paarweise(dom, [0, 1, 2], A.Zaehler())
    assert dom == [{1}, {2}, {3}] and ch == {1, 2}


def test_paarweise_doppelter_wert_ist_widerspruch():
    assert A.prop_paarweise([{2}, {2}, {1, 2, 3}], [0, 1, 2], A.Zaehler()) is None


def test_bounds_hall_verletzung_und_intervall():
    assert A.prop_bounds([{1, 2}, {1, 2}, {1, 2}], [0, 1, 2], A.Zaehler()) is None        # drei Variablen im Intervall [1, 2]
    dom = [{1, 2}, {1, 2}, {1, 2, 3, 4}]
    assert A.prop_bounds(dom, [0, 1, 2], A.Zaehler()) == {2} and dom[2] == {3, 4}            # [1, 2] gehört x1, x2


def test_matching_groesse_von_hand():
    z = A.Zaehler()
    assert A.max_matching([{1}, {1}, {1, 2}], [0, 1, 2], z)[2] == 2         # x1 und x2 wollen beide die 1: Größe 2 von 3 möglichen
    assert A.max_matching([{1, 2}, {1}, {2, 3}], [0, 1, 2], z)[2] == 3


def test_hall_menge_h2(h2):
    mate_var, mate_val, _ = A.max_matching(h2.dom_liste(), [0, 1, 2, 3], A.Zaehler())
    menge, werte = A.hall_menge(h2.dom_liste(), mate_var, mate_val, 1)
    assert menge == [0, 1] and werte == [1, 3]                            # Wert 1 gehört x1, x2, die sich {1, 3} teilen


def test_zaehler_zaehlen_aufrufe_und_operationen():
    z = A.Zaehler()
    A.propagiere_gruppe([{1}, {1, 2}], [0, 1], "A", z)
    assert z.aufrufe == 1 and z.ops_dom > 0 and z.ops_kanten == 0 and z.ops == z.ops_dom
    z = A.Zaehler()
    A.propagiere_gruppe([{1, 2}, {1, 2}, {1, 2, 3}], [0, 1, 2], "C", z)
    assert z.aufrufe == 1 and z.ops_kanten > 0


def test_unbekanntes_ereignis_wirft():
    with pytest.raises(ValueError):
        A.beschreibe({"art": "gibt-es-nicht"})
