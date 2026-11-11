"""Permalink (Begrenzen), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio)."""

import time
from dataclasses import dataclass

import streamlit as st

import ald_constants as C
from ald_rng import SplitMix64


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None


SETTING_SPECS = {
    "stufe_select": SettingSpec("stufe", str, C.DEFAULT_STUFE, options=C.STUFEN),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "budget_slider": SettingSpec("budget", int, C.DEFAULT_BUDGET, options=C.BUDGET_OPTIONEN),
    "beispiel_select": SettingSpec("beispiel", str, C.BEISPIEL_H2, options=C.BEISPIELE),
    "eigene_input": SettingSpec("domaenen", str, C.EIGENE_STANDARD),
    "hall_k_slider": SettingSpec("k", int, C.DEFAULT_HALL_K, C.HALL_K_MIN, C.HALL_K_MAX),
    "hall_m_slider": SettingSpec("m", int, C.DEFAULT_HALL_M, C.HALL_M_MIN, C.HALL_M_MAX),
    "hall_frei_radio": SettingSpec("frei", int, C.DEFAULT_HALL_FREI, options=C.HALL_FREI_OPTIONEN),
    "ordnung_slider": SettingSpec("ordnung", int, C.DEFAULT_ORDNUNG, C.ORDNUNG_MIN, C.ORDNUNG_MAX),
    "lueck_slider": SettingSpec("luecken", int, C.DEFAULT_LUECKE, C.LUECKE_MIN, C.LUECKE_MAX),
}
PRESET_KEYS = {
    "stufe": "stufe_select", "seed": "seed_input", "budget": "budget_slider", "beispiel": "beispiel_select", "eigene": "eigene_input",
    "hall_k": "hall_k_slider", "hall_m": "hall_m_slider", "hall_frei": "hall_frei_radio", "ordnung": "ordnung_slider", "luecken": "lueck_slider",
}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def _bereinige(spec, wert):
    """Wert aus der Adresszeile auf die Reglergrenzen begrenzen beziehungsweise auf erlaubte Optionen prüfen; None = verwerfen."""
    if spec.options is not None:
        return wert if wert in spec.options else None
    if spec.caster is str:
        return wert[: C.TEXT_MAX]
    if spec.lo is not None:
        wert = max(spec.lo, wert)
    if spec.hi is not None:
        wert = min(spec.hi, wert)
    return wert


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                wert = _bereinige(spec, spec.caster(qp[spec.url_param]))
            except (ValueError, TypeError):
                continue
            if wert is not None:
                st.session_state[state_key] = wert
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    """Ein Preset setzt alle Regler: was es nicht nennt, bekommt den Standardwert."""
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name].get(key, SETTING_SPECS[state_key].default)


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    """Neuer Zufalls-Seed der Rotationspläne; der Strom kommt aus dem SplitMix64 des Repos, gespeist von der Uhr."""
    st.session_state["seed_input"] = SplitMix64(time.time_ns()).below(C.SEED_MAX + 1)
