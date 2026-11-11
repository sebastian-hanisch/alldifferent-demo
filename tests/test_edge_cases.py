"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): leere Domäne, einelementige Domänen, doppelt vorbelegter Wert,
Gruppe mit einer Variablen, Wertebereich mit Lücken und negativen Werten, mehr Werte als Variablen, Ordnung 1 und 2."""

import pytest

import ald_algorithm as A
import ald_evaluation as E
import ald_scenario as S
from conftest import lauf, wurzel


@pytest.mark.parametrize("stufe", "ABC")
def test_leere_domaene_ist_sofortiger_fehlschlag(stufe):
    inst = S.aus_domaenen([set(), {1, 2}])
    r = lauf(inst, stufe)
    assert (r.antwort, r.knoten, r.fehlschlaege) == ("unloesbar", 1, 1)


@pytest.mark.parametrize("stufe", "ABC")
def test_doppelt_vorbelegter_wert_ist_sofortiger_fehlschlag(stufe):
    r = lauf(S.aus_domaenen([{3}, {3}, {1, 2, 3}]), stufe)
    assert (r.antwort, r.knoten) == ("unloesbar", 1)
    r = lauf(S.rotationsplan(4, {(0, 0): 2, (0, 3): 2}), stufe)      # zwei gleiche Schichten in einer Zeile
    assert r.antwort == "unloesbar" and r.knoten == 1


@pytest.mark.parametrize("stufe", "ABC")
def test_einelementige_domaenen_und_gruppe_mit_einer_variablen(stufe):
    r = lauf(S.aus_domaenen([{5}, {7}, {9}]), stufe)
    assert (r.antwort, r.knoten, r.loesung) == ("loesbar", 1, (5, 7, 9))
    r = lauf(S.aus_domaenen([{1, 2, 3}]), stufe)
    assert r.antwort == "loesbar" and r.loesung == (1,) and r.knoten == 2    # Wurzel und der erste Wert
    assert lauf(S.aus_domaenen([{1, 2, 3}]), stufe, alle=True).loesungen == 3


@pytest.mark.parametrize("stufe", "ABC")
def test_mehr_werte_als_variablen_und_negative_werte_mit_luecken(stufe):
    inst = S.aus_domaenen([{-3, 0, 10}, {-3, 10}, {0, 10, 11, 12}])
    erwartet = [(a, b, c) for a in (-3, 0, 10) for b in (-3, 10) for c in (0, 10, 11, 12) if len({a, b, c}) == 3]
    r = lauf(inst, stufe, alle=True)
    assert r.loesungen == len(erwartet) and r.loesung in erwartet


@pytest.mark.parametrize("stufe", "ABC")
def test_ordnung_1_und_2(stufe):
    assert lauf(S.rotationsplan(1, {}), stufe).loesung == (1,)
    assert lauf(S.rotationsplan(2, {}), stufe, alle=True).loesungen == 2       # die zwei lateinischen Quadrate der Ordnung 2
    assert lauf(S.rotationsplan(2, {(0, 0): 1, (1, 1): 1}), stufe, alle=True).loesungen == 1     # die Diagonale 1, 1 erzwingt (0,1) = (1,0) = 2
    assert lauf(S.rotationsplan(2, {(0, 0): 1, (1, 1): 2}), stufe).antwort == "unloesbar"       # (0,1) müsste 2 sein und stünde über (1,1) = 2 in derselben Spalte
    assert S.lateinisches_quadrat(1, 5) == [[1]]
    assert sorted(map(tuple, S.lateinisches_quadrat(2, 5))) in ([(1, 2), (2, 1)], [(2, 1), (1, 2)])


def test_hall_instanz_mit_k_gleich_3_und_ohne_freie_variablen():
    inst = S.hall_instanz(3, 0)
    assert inst.n == 4 and wurzel(inst, "C") is None


def test_wurzel_ohne_widerspruch_hat_festgelegt_wurzel_sonst_none():
    ok = lauf(S.h2_loecher(), "C")
    assert ok.festgelegt_wurzel == 2
    assert lauf(S.hall_instanz(4, 0), "C").festgelegt_wurzel is None


def test_parse_domaenen_gueltig_und_ungueltig():
    assert E.parse_domaenen("1 3; 1 3; 1 2 3") == [{1, 3}, {1, 3}, {1, 2, 3}]
    assert E.parse_domaenen("1,2 ; 2") == [{1, 2}, {2}]
    for schlecht in ("", "1 2", "1 2;;3", "1 a; 2", "0 1; 2", "1 9; 2", "; ".join(["1"] * 9)):
        with pytest.raises(ValueError):
            E.parse_domaenen(schlecht)


def test_beispiel_instanz_eigene_domaenen_gibt_eine_gruppe():
    inst = E.beispiel_instanz(E.C.BEISPIEL_EIGEN, "1 2; 1 2; 3")
    assert inst.n == 3 and inst.gruppen == ((0, 1, 2),)


def test_beschreibung_hall_verletzung_und_matching():
    assert "mehr Variablen als Werte" in A.beschreibe({"art": "hall_verletzung", "intervall": (1, 3), "menge": [0, 1, 2, 3]})
    assert "nur 3 Kanten" in A.beschreibe({"art": "kein_matching", "groesse": 3, "anzahl": 4})
