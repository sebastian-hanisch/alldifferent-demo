"""Zufallsgenerator und Instanzerzeuger: Regressionswerte des SplitMix64, Gleichheit mit dem Original, gültige lateinische Quadrate, Vorbelegung."""

import importlib.util
from pathlib import Path

import pytest

import ald_scenario as S
from ald_rng import SplitMix64, mische, ziehe_zwei

ORIGINAL = Path(__file__).resolve().parent.parent.parent / "reduktionskette-demo" / "red_scenario.py"


def test_splitmix_bekannte_werte():
    """Veröffentlichte Referenzwerte der SplitMix64-Konvention (Vigna) für den Seed 0."""
    g = SplitMix64(0)
    assert [g.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]
    assert SplitMix64(12345).next() == 2454886589211414944


@pytest.mark.skipif(not ORIGINAL.exists(), reason="reduktionskette-demo liegt nicht neben diesem Repo (CI)")
def test_splitmix_gleich_dem_original():
    spec = importlib.util.spec_from_file_location("red_scenario_original", ORIGINAL)
    red = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(red)
    a, b = SplitMix64(99), red.SplitMix64(99)
    assert [a.next() for _ in range(50)] == [b.next() for _ in range(50)]
    assert SplitMix64(7).below(10) == red.SplitMix64(7).below(10) and SplitMix64(8).coin() == red.SplitMix64(8).coin()


def test_mische_ist_eine_deterministische_permutation():
    liste = list(range(20))
    mische(SplitMix64(3), liste)
    assert sorted(liste) == list(range(20)) and liste != list(range(20))
    zweite = list(range(20))
    mische(SplitMix64(3), zweite)
    assert zweite == liste


def test_ziehe_zwei_liefert_verschiedene_zahlen_und_trifft_jedes_paar():
    rng = SplitMix64(1)
    gesehen = set()
    for _ in range(400):
        a, b = ziehe_zwei(rng, 4)
        assert a != b and 0 <= a < 4 and 0 <= b < 4
        gesehen.add((a, b))
    assert len(gesehen) == 12                                    # alle 4 * 3 geordneten Paare kommen vor


def _ist_latein(q):
    n = len(q)
    return all(sorted(z) == list(range(1, n + 1)) for z in q) and all(sorted(q[r][c] for r in range(n)) == list(range(1, n + 1)) for c in range(n))


def test_lateinische_quadrate_sind_gueltig_deterministisch_und_durchmischt():
    for n in (3, 4, 7, 10, 15):
        q = S.lateinisches_quadrat(n, 11)
        assert _ist_latein(q) and q == S.lateinisches_quadrat(n, 11)
    zyklisch = [[(r + c) % 10 + 1 for c in range(10)] for r in range(10)]
    q = S.lateinisches_quadrat(10, 11)
    assert sum(q[r][c] != zyklisch[r][c] for r in range(10) for c in range(10)) > 80      # nach 3000 Tauschen kaum noch Zellen des Ausgangsquadrats
    assert q != S.lateinisches_quadrat(10, 12)


def test_regressionswert_des_erzeugers_gleicher_strom_auf_jeder_plattform():
    assert S.lateinisches_quadrat(4, 7) == [[4, 2, 3, 1], [2, 4, 1, 3], [1, 3, 2, 4], [3, 1, 4, 2]]


@pytest.mark.parametrize("ordnung,prozent,erwartet", [(10, 58, 42), (12, 58, 60), (15, 55, 101), (5, 50, 13), (6, 50, 18), (10, 100, 0)])
def test_anzahl_vorbelegt_rundet_ganzzahlig_nach_oben_bei_halben(ordnung, prozent, erwartet):
    """Von Hand: 100 * 0,42 = 42; 144 * 0,42 = 60,48 -> 60; 225 * 0,45 = 101,25 -> 101; 25 * 0,5 = 12,5 -> 13 (0,5 nach oben); 36 * 0,5 = 18."""
    assert S.anzahl_vorbelegt(ordnung, prozent) == erwartet


def test_rotationsplan_instanz_ist_erfuellbar_nach_konstruktion():
    for ordnung, prozent, seed in ((6, 50, 3), (10, 58, 0), (12, 62, 5), (15, 35, 1)):
        inst, quadrat = S.rotationsplan_instanz(ordnung, prozent, seed)
        fest = [i for i, d in enumerate(inst.doms) if len(d) == 1]
        assert len(fest) == S.anzahl_vorbelegt(ordnung, prozent)
        flach = tuple(v for zeile in quadrat for v in zeile)
        assert S.ist_loesung(inst, flach)
        assert all(inst.doms[i] == frozenset({flach[i]}) for i in fest)
        assert inst == S.rotationsplan_instanz(ordnung, prozent, seed)[0]


def test_ist_loesung_ist_ein_unabhaengiger_pruefer():
    inst = S.h3_rotationsplan()
    gut = (1, 2, 3, 4, 2, 1, 4, 3, 3, 4, 1, 2, 4, 3, 2, 1)
    assert S.ist_loesung(inst, gut)
    assert not S.ist_loesung(inst, gut[:-1] + (2,))                     # Zelle (3,3) = 2: die 2 steht dann doppelt in Zeile 3
    assert not S.ist_loesung(inst, (2,) + gut[1:])                       # Zelle (0,0) = 2: doppelt in Zeile 0 und in Spalte 0
    assert not S.ist_loesung(inst, None)
    assert not S.ist_loesung(inst, (5,) + gut[1:])                       # Wert 5 liegt in keiner Domäne
