"""Eigenschaftstests: jede Stärke schneidet nie eine Lösung ab, Propagation ist idempotent und monoton, C ⊆ B ⊆ A,
Umbenennen der Werte ändert die Antwort nie, Hall-Verletzung scheitert in B und C an der Wurzel, und jede Stärke weicht auf mindestens einer Instanz
von ihrer Nachbarin ab (Zweig-Test: keine Spalte mit lauter gleichen Werten)."""

import ald_algorithm as A
import ald_scenario as S
import ald_search as Q
from ald_rng import SplitMix64
from conftest import alle_belegungen, lauf, wurzel
from test_oracle_alldifferent import zufalls_domaenen


def _wurzeln(doms):
    return {s: wurzel(S.aus_domaenen(doms), s) for s in "ABC"}


def test_keine_stufe_schneidet_eine_loesung_ab():
    rng = SplitMix64(1)
    for fall in range(200):
        p = 3 + rng.below(4)
        doms = zufalls_domaenen(rng, p, list(range(1, 8)), 30 + rng.below(40))
        loesungen = alle_belegungen(doms)
        for s, d in _wurzeln(doms).items():
            if not loesungen:
                continue                      # ohne Lösung darf jede Stärke scheitern oder nicht (A merkt es nicht immer)
            assert d is not None, (fall, s)
            assert all(b[i] in d[i] for b in loesungen for i in range(p)), (fall, s)


def test_teilmengenordnung_c_in_b_in_a_und_zweig_test():
    rng = SplitMix64(2)
    b_staerker, c_staerker = 0, 0
    for fall in range(300):
        p = 3 + rng.below(4)
        doms = zufalls_domaenen(rng, p, list(range(1, 7)), 45 + rng.below(35))
        w = _wurzeln(doms)
        if w["A"] is None:
            continue
        if w["B"] is None:
            assert w["C"] is None
            continue
        assert all(set(b) <= set(a) for a, b in zip(w["A"], w["B"]))
        if w["C"] is not None:
            assert all(set(c) <= set(b) for b, c in zip(w["B"], w["C"]))
        b_staerker += w["B"] != w["A"]
        c_staerker += w["C"] != w["B"]
    assert b_staerker >= 5 and c_staerker >= 5, (b_staerker, c_staerker)   # jede Stärke streicht auf mindestens einer Instanz mehr als die Nachbarin


def test_propagation_ist_idempotent_und_monoton():
    rng = SplitMix64(3)
    for fall in range(150):
        p = 3 + rng.below(4)
        doms = zufalls_domaenen(rng, p, list(range(1, 8)), 40)
        for s in "ABC":
            dom = [set(d) for d in doms]
            g = list(range(p))
            if A.propagiere_gruppe(dom, g, s, A.Zaehler()) is None:
                continue
            assert all(dom[i] <= doms[i] for i in range(p))                      # Domänen werden nie größer
            nochmal = [set(d) for d in dom]
            assert A.propagiere_gruppe(nochmal, g, s, A.Zaehler()) == set() and nochmal == dom   # zweiter Lauf ändert nichts


def test_umbenennen_der_werte_aendert_die_antwort_nie():
    rng = SplitMix64(4)
    perm = {w: w2 for w, w2 in zip(range(1, 8), [5, 3, 7, 1, 6, 2, 4])}
    for fall in range(100):
        p = 3 + rng.below(3)
        doms = zufalls_domaenen(rng, p, list(range(1, 8)), 45)
        umbenannt = [{perm[w] for w in d} for d in doms]
        for s in "ABC":
            a = lauf(S.aus_domaenen(doms), s)
            b = lauf(S.aus_domaenen(umbenannt), s)
            assert (a.antwort, a.loesungen) == (b.antwort, b.loesungen), (fall, s)


def test_hall_verletzung_scheitert_in_b_und_c_an_der_wurzel_und_a_waechst():
    knoten_a = []
    for k in range(3, 8):
        inst = S.hall_instanz(k, 0)
        assert lauf(inst, "B").knoten == 1 and lauf(inst, "C").knoten == 1
        assert wurzel(inst, "B") is None and wurzel(inst, "C") is None
        assert wurzel(inst, "A") is not None                                    # die paarweise Prüfung sieht nichts
        knoten_a.append(lauf(inst, "A").knoten)
    assert all(b > a for a, b in zip(knoten_a, knoten_a[1:])) and knoten_a[0] == 10


def test_zweig_test_knotenzahlen_laufen_auf_grossen_instanzen_auseinander():
    """Mindestens ein Rotationsplan der Ordnung 12, auf dem A mehr Knoten braucht als B und B mehr als C (keine Spalte mit lauter gleichen Werten)."""
    gefunden = 0
    for seed in range(20):
        inst, _ = S.rotationsplan_instanz(12, 58, seed)
        k = {s: lauf(inst, s, budget=5000).knoten for s in "ABC"}
        gefunden += k["A"] > k["B"] > k["C"]
    assert gefunden >= 1


def test_budget_bricht_ab_und_zaehlt_genau_das_budget():
    r = lauf(S.hall_instanz(7, 0), "A", budget=100)
    assert r.antwort == "abgebrochen" and r.knoten == 100 and r.loesung is None
    assert lauf(S.hall_instanz(7, 0), "C", budget=100).antwort == "unloesbar"


def test_wurzel_propagation_zaehlt_wie_die_suche():
    inst = S.h3_rotationsplan()
    ok, dom, spur, z = Q.wurzel_propagation(inst.dom_liste(), inst.gruppen, "C", spur=True)
    suche = lauf(inst, "C")
    assert ok and suche.wurzel == tuple(tuple(sorted(d)) for d in dom)
    assert all("gruppe" in e for e in spur)
