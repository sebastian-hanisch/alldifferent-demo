"""Orakel-Tests: Kern gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §5, DEMO-PLAYBOOK §12).

  * Bereichskonsistenz (Stufe C, Régin) gegen die Aufzählung aller Belegungen;
  * Bounds-Konsistenz (Stufe B) gegen ihre Definition per Aufzählung (Relaxierung auf die Intervalle der Domänen);
  * maximales Matching gegen `scipy.sparse.csgraph.maximum_bipartite_matching`;
  * Lösungszahl der Rotationspläne (Ordnung 4) gegen Aufzählung aller 576 lateinischen Quadrate;
  * Erfüllbarkeit gegen OR-Tools CP-SAT (Ordnung 8 bis 12, nur im Test-venv, nie in der App);
  * Hall-Menge der Régin-Streichung gegen die Definition (so viele Werte wie Variablen, Variable ausgeschlossen).
Die Zufallsfälle kommen aus dem SplitMix64 des Repos (feste Seeds), nie aus Pythons `random`."""

import itertools

import pytest

import ald_algorithm as A
import ald_scenario as S
from ald_rng import SplitMix64
from conftest import alle_belegungen, lauf


def zufalls_domaenen(rng, p, wertebereich, dichte):
    """p Domänen aus wertebereich; jeder Wert mit Wahrscheinlichkeit dichte/100, mindestens ein Wert."""
    doms = []
    for _ in range(p):
        d = {w for w in wertebereich if rng.below(100) < dichte}
        doms.append(d or {wertebereich[rng.below(len(wertebereich))]})
    return doms


def propagiere_einmal(doms, stufe):
    dom = [set(d) for d in doms]
    z = A.Zaehler()
    ergebnis = A.propagiere_gruppe(dom, list(range(len(dom))), stufe, z)
    return (None if ergebnis is None else dom), z


# ------------------------------------------------------------------------------------------------------------------------------------
# Bereichskonsistenz per Aufzählung
# ------------------------------------------------------------------------------------------------------------------------------------
def test_regin_gleich_bereichskonsistenz_per_aufzaehlung():
    rng = SplitMix64(2026)
    schwer = 0
    for fall in range(300):
        p = 3 + rng.below(4)                                          # Gruppengröße 3..6
        bereich = list(range(-2, 6)) if fall % 5 == 0 else list(range(1, 8))   # auch negative Werte
        doms = zufalls_domaenen(rng, p, bereich, 35 + rng.below(40))
        erwartet = alle_belegungen(doms)
        ergebnis, _ = propagiere_einmal(doms, "C")
        if not erwartet:
            assert ergebnis is None, (fall, doms)
            continue
        stuetzen = [{b[i] for b in erwartet} for i in range(p)]
        assert ergebnis == stuetzen, (fall, doms)
        schwer += any(set(d) != s for d, s in zip(doms, stuetzen))
    assert schwer >= 50, "zu wenige Fälle, in denen Régin überhaupt streicht: das Orakel prüfte fast nichts"


# ------------------------------------------------------------------------------------------------------------------------------------
# Bounds-Konsistenz per Definition
# ------------------------------------------------------------------------------------------------------------------------------------
def huelle(doms):
    return [set(range(min(d), max(d) + 1)) for d in doms]


def test_bounds_gegen_ihre_definition_per_aufzaehlung():
    """Definition: jede Schranke (kleinster und größter Wert) einer Domäne hat eine Stütze im auf die Intervalle relaxierten Problem.
    Dazu Korrektheit (keine Lösung des echten Problems geht verloren) und: Hall-Verletzung der Intervalle bedeutet Fehlschlag."""
    rng = SplitMix64(77)
    streichungen = 0
    for fall in range(300):
        p = 3 + rng.below(4)
        doms = zufalls_domaenen(rng, p, list(range(1, 8)), 30 + rng.below(45))
        echt = alle_belegungen(doms)
        relaxiert_vorher = alle_belegungen(huelle(doms))
        ergebnis, _ = propagiere_einmal(doms, "B")
        if not relaxiert_vorher:
            assert ergebnis is None, (fall, doms)           # Hall-Verletzung (Intervalle) muss erkannt werden
            continue
        if ergebnis is None:
            assert not echt, (fall, doms)                    # Fehlschlag nur, wenn es wirklich keine Lösung gibt
            continue
        for b in echt:                                       # keine Lösung geht verloren
            assert all(b[i] in ergebnis[i] for i in range(p)), (fall, doms)
        relaxiert = alle_belegungen(huelle(ergebnis))
        for i in range(p):
            assert any(b[i] == min(ergebnis[i]) for b in relaxiert), (fall, doms, ergebnis)
            assert any(b[i] == max(ergebnis[i]) for b in relaxiert), (fall, doms, ergebnis)
        streichungen += sum(len(d) - len(e) for d, e in zip(doms, ergebnis))
    assert streichungen > 100


# ------------------------------------------------------------------------------------------------------------------------------------
# Matching
# ------------------------------------------------------------------------------------------------------------------------------------
def test_matching_gegen_scipy():
    sp = pytest.importorskip("scipy.sparse")
    csgraph = pytest.importorskip("scipy.sparse.csgraph")
    rng = SplitMix64(5)
    for fall in range(200):
        p = 2 + rng.below(6)
        doms = zufalls_domaenen(rng, p, list(range(1, 8)), 25 + rng.below(40))
        _, _, groesse = A.max_matching(doms, list(range(p)), A.Zaehler())
        zeilen = [i for i, d in enumerate(doms) for _ in d]
        spalten = [w - 1 for d in doms for w in sorted(d)]
        m = sp.csr_matrix(([1] * len(zeilen), (zeilen, spalten)), shape=(p, 7))
        match = csgraph.maximum_bipartite_matching(m, perm_type="column")
        assert groesse == int((match >= 0).sum()), (fall, doms)


# ------------------------------------------------------------------------------------------------------------------------------------
# Rotationspläne
# ------------------------------------------------------------------------------------------------------------------------------------
def _alle_quadrate_ordnung_4():
    perms = list(itertools.permutations(range(1, 5)))
    quadrate = []
    for a in perms:
        for b in perms:
            if any(x == y for x, y in zip(a, b)):
                continue
            for c in perms:
                if any(c[i] in (a[i], b[i]) for i in range(4)):
                    continue
                for d in perms:
                    if all(d[i] not in (a[i], b[i], c[i]) for i in range(4)):
                        quadrate.append(a + b + c + d)
    return quadrate


def test_loesungszahl_ordnung_4_gegen_aufzaehlung_aller_576_quadrate():
    quadrate = _alle_quadrate_ordnung_4()
    assert len(quadrate) == 576                                     # bekannte Zahl der lateinischen Quadrate der Ordnung 4
    rng = SplitMix64(11)
    for fall in range(40):
        vorbelegt = {}
        for _ in range(rng.below(5)):                               # 0 bis 4 Vorbelegungen
            vorbelegt[(rng.below(4), rng.below(4))] = 1 + rng.below(4)
        inst = S.rotationsplan(4, vorbelegt)
        erwartet = [q for q in quadrate if all(q[r * 4 + c] == v for (r, c), v in vorbelegt.items())]
        for stufe in "ABC":
            erg = lauf(inst, stufe, alle=True)
            assert erg.loesungen == len(erwartet), (fall, stufe, vorbelegt)
            assert (erg.antwort == "loesbar") == bool(erwartet)
            if erwartet:
                assert erg.loesung in erwartet


def test_erfuellbarkeit_gegen_cpsat_ordnung_8_bis_12():
    cp_model = pytest.importorskip("ortools.sat.python.cp_model")

    def cpsat(inst):
        m = cp_model.CpModel()
        x = [m.NewIntVarFromDomain(cp_model.Domain.FromValues(sorted(d)), f"x{i}") for i, d in enumerate(inst.doms)]
        for g in inst.gruppen:
            m.AddAllDifferent([x[i] for i in g])
        s = cp_model.CpSolver()
        s.parameters.num_workers = 1
        s.parameters.max_time_in_seconds = 30
        r = s.Solve(m)
        assert r != cp_model.UNKNOWN
        return r in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    unerfuellbar = 0
    for ordnung in (8, 10, 12):
        for seed in range(4):
            inst, _ = S.rotationsplan_instanz(ordnung, 58, seed)
            # eine zweite Fassung mit einer Vorbelegung, die einen Nachbarn in derselben Zeile verdoppelt: oft unerfüllbar
            vorbelegt = {(i // ordnung, i % ordnung): next(iter(d)) for i, d in enumerate(inst.doms) if len(d) == 1}
            zellen = sorted(vorbelegt)
            (r, c), (r2, c2) = zellen[0], zellen[1]
            vorbelegt[(r2, c2)] = vorbelegt[(r, c)] if r == r2 else (vorbelegt[(r2, c2)] % ordnung) + 1
            for variante in (inst, S.rotationsplan(ordnung, vorbelegt)):
                erwartet = cpsat(variante)
                unerfuellbar += not erwartet
                erg = lauf(variante, "C", budget=20000)
                assert erg.antwort != "abgebrochen"
                assert (erg.antwort == "loesbar") == erwartet, (ordnung, seed)
                if erwartet:
                    assert S.ist_loesung(variante, erg.loesung)
    assert unerfuellbar >= 1, "keine unerfüllbare Variante: die Gegenprobe prüfte nur die Erfüllbarkeit"


# ------------------------------------------------------------------------------------------------------------------------------------
# Hall-Menge der Régin-Streichungen
# ------------------------------------------------------------------------------------------------------------------------------------
def test_hall_menge_jeder_regin_streichung_gegen_die_definition():
    """Zu jeder Streichung (j, w): die Menge S hat so viele Variablen wie Werte, ihre Domänen liegen in den Werten von S, j liegt nicht in S, w liegt in den Werten."""
    rng = SplitMix64(31)
    pruefungen = 0
    for fall in range(200):
        p = 3 + rng.below(4)
        doms = zufalls_domaenen(rng, p, list(range(1, 8)), 30 + rng.below(40))
        dom = [set(d) for d in doms]
        spur = []
        if A.propagiere_gruppe(dom, list(range(p)), "C", A.Zaehler(), spur) is None:
            continue
        for e in spur:
            assert e["art"] == "hall_menge"
            menge, werte = e["menge"], set(e["wertmenge"])
            assert len(menge) == len(werte) and e["var"] not in menge and e["werte"][0] in werte
            assert set().union(*[doms[u] for u in menge]) == werte
            pruefungen += 1
    assert pruefungen >= 100
