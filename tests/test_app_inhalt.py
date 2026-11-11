"""AppTest: Inhalte der vier Reiter an den Presets (Verdikt-Zeilen, Fehlermeldung bei ungültigen Domänen, Knopf der teuren Rechnung)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import ald_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at) -> str:
    teile = [m.value for m in at.markdown] + [s.value for s in at.success] + [i.value for i in at.info] + [w.value for w in at.warning] + [e.value for e in at.error]
    return "\n".join(teile)


def test_standard_zeigt_kernfrage_und_h2_verdikt():
    text = _texte(_app())
    assert "nach 175 Knoten (96 Fehlschläge)" in text                              # Kernfrage an H1
    assert "C Régin: 2 von 4 Variablen festgelegt, 4 Werte gestrichen" in text      # Reiter 1, H2


def test_preset_h3_zeigt_4_6_8_festgelegte_zellen():
    at = _app()
    at.sidebar.button(key="preset_Handbeispiel H3 (Rotationsplan 4 × 4)").click().run()
    assert not at.exception
    text = _texte(at)
    assert "A paarweise: 4 von 16" in text and "B Bounds: 6 von 16" in text and "C Régin: 8 von 16" in text


def test_preset_hall_k5_zeigt_206_knoten():
    at = _app()
    at.sidebar.button(key="preset_Hall-Verletzung k = 5").click().run()
    assert not at.exception
    assert "Bei k = 5 (6 Variablen auf 5 Werte, ohne freie Variablen)" in _texte(at) and "nach 206 Knoten" in _texte(at)


def test_ungueltige_eigene_domaenen_geben_eine_fehlermeldung_statt_eines_absturzes():
    at = _app()
    at.selectbox(key="beispiel_select").set_value(C.BEISPIEL_EIGEN).run()
    at.text_input(key="eigene_input").set_value("1 a; 2").run()
    assert not at.exception
    assert any("keine ganze Zahl" in e.value for e in at.error)
    at.text_input(key="eigene_input").set_value("1 2; 1 2; 1 2").run()           # drei Variablen auf zwei Werte: Hall-Verletzung
    assert not at.exception and not at.error
    assert "Widerspruch an der Wurzel" in _texte(at)


def test_teure_hall_rechnung_startet_erst_auf_knopfdruck():
    at = _app()
    at.slider(key="hall_m_slider").set_value(2).run()
    assert not at.exception
    assert "noch nichts gerechnet" in _texte(at)
    at.slider(key="hall_k_slider").set_value(4).run()
    at.button(key="hall_rechnen").click().run()
    assert not at.exception
    assert "mit 2 freien Variablen" in _texte(at)


def test_rotationsplan_12_preset_rechnet_einzelinstanz_und_zeigt_den_sweep():
    at = _app()
    at.sidebar.button(key="preset_Rotationsplan 12").click().run()
    assert not at.exception
    text = _texte(at)
    assert "Ordnung 12 mit 58 % Lücken: A braucht" in text and "Ordnung 12, 58 % Lücken, 20 feste Zufalls-Seeds" in text
    assert "Régin braucht" in text                                                 # Reiter „Kosten je Aufruf“
