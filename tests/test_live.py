"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige (ald_live.py). Der Zwischenspeicher ändert keine Zahl: gespeichert gleich ungespeichert (bitgleich),
ein anderer Parameter kommt nie aus dem Speicher, ein zweiter Aufruf mit denselben Parametern rechnet nicht noch einmal."""

import ald_constants as C
import ald_evaluation as E
import ald_live as L
import ald_search as Q
from streamlit.testing.v1 import AppTest

KEY = (8, 50, 11, 2000)      # Ordnung, Lücken in Prozent, Zufalls-Seed, Knotenbudget


def _zaehler(monkeypatch):
    aufrufe = []
    echt = Q.loese

    def zaehlend(*args, **kwargs):
        aufrufe.append(args[2])
        return echt(*args, **kwargs)

    monkeypatch.setattr(Q, "loese", zaehlend)
    return aufrufe


def test_stufe_gespeichert_gleich_ungespeichert_und_gleich_rotationsplan_laeufe():
    L.rotation_stufe.clear()
    ref = E.rotationsplan_laeufe(*KEY)
    for s in C.STUFEN:
        roh, _ = L.rotation_stufe_ungespeichert(*KEY, s)
        assert roh == ref[s]
        assert L.rotation_stufe(*KEY, s)[0] == roh
        assert L.rotation_stufe(*KEY, s)[0] == roh
    laeufe, sek = L.rotation_aus_speicher(*KEY)
    assert laeufe == ref and sek >= 0


def test_zweiter_aufruf_rechnet_nicht_anderer_parameter_schon(monkeypatch):
    L.rotation_stufe.clear()
    aufrufe = _zaehler(monkeypatch)
    L.rotation_stufe(*KEY, "C")
    L.rotation_stufe(*KEY, "C")
    assert aufrufe == ["C"]
    ordnung, luecken, seed, budget = KEY
    a = L.rotation_stufe(ordnung, luecken, seed + 1, budget, "C")        # anderer Zufalls-Seed
    b = L.rotation_stufe(ordnung, luecken, seed, budget, "A")            # andere Stärke
    c = L.rotation_stufe(ordnung, luecken + 5, seed, budget, "C")        # andere Lücken
    d = L.rotation_stufe(ordnung, luecken, seed, budget // 2, "C")       # anderes Budget
    assert len(aufrufe) == 5
    assert a[0] == E.rotationsplan_stufe(ordnung, luecken, seed + 1, budget, "C") and b[0] == E.rotationsplan_stufe(*KEY, "A")
    assert c[0] == E.rotationsplan_stufe(ordnung, luecken + 5, seed, budget, "C") and d[0] == E.rotationsplan_stufe(ordnung, luecken, seed, budget // 2, "C")


def test_fortschrittsanzeige_liefert_ergebnisse_in_reihenfolge_und_ohne_fehler():
    def skript():
        import streamlit as st
        import ald_live as L

        erg = L.mit_fortschritt("Probe", [("eins", (1,)), ("zwei", (2,)), ("drei", (3,))], lambda x: x * 10)
        st.write(f"ergebnis {erg}")

    at = AppTest.from_function(skript)
    at.run(timeout=60)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("ergebnis [10, 20, 30]" in m.value for m in at.markdown)


def test_rotation_mit_fortschritt_in_der_app_ohne_fehler():
    def skript():
        import streamlit as st
        import ald_live as L

        laeufe, sek = L.rotation(8, 50, 11, 2000)
        st.write(f"stufen {list(laeufe)}")

    at = AppTest.from_function(skript)
    at.run(timeout=120)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("stufen ['A', 'B', 'C']" in m.value for m in at.markdown)
