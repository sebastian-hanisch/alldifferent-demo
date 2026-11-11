"""Gemeinsame Fixtures und Hilfen: Handbeispiele H1 bis H3 (von Hand gerechnet, Plan Stück 10) und kleine Hilfsfunktionen für die Orakel."""

import itertools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ald_scenario as S  # noqa: E402
import ald_search as Q  # noqa: E402


def lauf(inst, stufe, **kw):
    """Suche auf einer Instanz mit einer Stärke."""
    return Q.loese(inst.dom_liste(), inst.gruppen, stufe, **kw)


def wurzel(inst, stufe):
    """Domänen nach der Wurzelpropagation als Liste sortierter Listen, None bei Fehlschlag."""
    ok, dom, _, _ = Q.wurzel_propagation(inst.dom_liste(), inst.gruppen, stufe)
    return [sorted(d) for d in dom] if ok else None


def alle_belegungen(doms):
    """Alle Belegungen mit paarweise verschiedenen Werten per Aufzählung (unabhängig vom Régin-Verfahren)."""
    return [c for c in itertools.product(*[sorted(d) for d in doms]) if len(set(c)) == len(c)]


@pytest.fixture
def h2():
    return S.h2_loecher()


@pytest.fixture
def h3():
    return S.h3_rotationsplan()
