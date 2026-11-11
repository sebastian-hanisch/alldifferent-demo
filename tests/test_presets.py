"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, Permalink-Bereinigung."""

import ald_constants as C
import ald_evaluation as ev
import ald_presets as P


def test_every_preset_has_help_and_only_known_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) <= set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_or_options():
    for name, preset in C.PRESETS.items():
        for key, value in preset.items():
            spec = P.SETTING_SPECS[P.PRESET_KEYS[key]]
            if spec.options is not None:
                assert value in spec.options, (name, key)
            else:
                assert spec.lo <= value <= spec.hi, (name, key)


def test_default_preset_is_empty_and_equals_the_default_settings():
    assert C.PRESETS[next(iter(C.PRESETS))] == {}
    assert ev.Settings() == ev.Settings(**{k: spec.default for k, spec in zip(
        ("stufe", "seed", "budget", "beispiel", "eigene", "hall_k", "hall_m", "hall_frei", "ordnung", "luecken"),
        (P.SETTING_SPECS[v] for v in P.PRESET_KEYS.values()))})


def test_every_preset_differs_from_the_default_in_exactly_the_keys_it_names():
    for name, preset in list(C.PRESETS.items())[1:]:
        assert preset, name
        for key, value in preset.items():
            assert value != P.SETTING_SPECS[P.PRESET_KEYS[key]].default, (name, key)


def test_setting_specs_cover_every_preset_key_and_url_params_are_unique():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    params = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(params) == len(set(params))


def test_permalink_bereinigung_begrenzt_und_verwirft_ungueltiges():
    assert P._bereinige(P.SETTING_SPECS["hall_k_slider"], 99) == C.HALL_K_MAX
    assert P._bereinige(P.SETTING_SPECS["hall_k_slider"], -5) == C.HALL_K_MIN
    assert P._bereinige(P.SETTING_SPECS["budget_slider"], 20000) == 20000
    assert P._bereinige(P.SETTING_SPECS["budget_slider"], 12345) is None
    assert P._bereinige(P.SETTING_SPECS["stufe_select"], "Z") is None
    assert P._bereinige(P.SETTING_SPECS["eigene_input"], "x" * 1000) == "x" * C.TEXT_MAX


def test_slider_bounds_enthalten_die_standardwerte_und_die_beispiele():
    assert C.HALL_K_MIN <= C.DEFAULT_HALL_K <= C.HALL_K_MAX and C.HALL_M_MIN <= C.DEFAULT_HALL_M <= C.HALL_M_MAX
    assert C.ORDNUNG_MIN <= C.DEFAULT_ORDNUNG <= C.ORDNUNG_MAX and C.LUECKE_MIN <= C.DEFAULT_LUECKE <= C.LUECKE_MAX
    assert C.DEFAULT_BUDGET in C.BUDGET_OPTIONEN and C.DEFAULT_HALL_FREI in C.HALL_FREI_OPTIONEN and C.DEFAULT_STUFE in C.STUFEN
    assert ev.parse_domaenen(C.EIGENE_STANDARD) == [{1, 3}, {1, 3}, {1, 2, 3}, {2, 3, 4}]    # der Ausgangspunkt ist H2
