"""Live-Knöpfe: Zwischenspeicher und Fortschrittsanzeige.

Die Einzelinstanz des Rotationsplans rechnet drei Stärken nacheinander. Jede Stärke ist eine Einheit, eine reine Funktion ihrer Parameter (die Instanz ist deterministisch),
und liegt einzeln im Zwischenspeicher (`st.cache_data`, kleine `max_entries`); die Anzeige zählt die fertigen Stärken (`mit_fortschritt`). Dieselbe Einstellung ein zweites Mal
antwortet aus dem Speicher. Die Ergebnisse sind bitgleich zu den ungespeicherten Funktionen (`tests/test_live.py`). Rechnung, Zahlen und Aussagen ändern sich nicht."""

import time

import streamlit as st

import ald_constants as C
import ald_evaluation as E


def rotation_stufe_ungespeichert(ordnung: int, luecken: int, seed: int, budget: int, stufe: str):
    """(Lauf, Rechenzeit in Sekunden) einer Stärke; die Zeit dient nur der Anzeige."""
    t0 = time.perf_counter()
    lauf = E.rotationsplan_stufe(ordnung, luecken, seed, budget, stufe)
    return lauf, time.perf_counter() - t0


@st.cache_data(show_spinner=False, max_entries=24)
def rotation_stufe(ordnung, luecken, seed, budget, stufe):
    return rotation_stufe_ungespeichert(ordnung, luecken, seed, budget, stufe)


def mit_fortschritt(titel: str, schritte: list, rechne) -> list:
    """Führt die Schritte nacheinander aus und zeigt, wie viele fertig sind. `schritte`: Liste aus (Beschriftung, Argumente); `rechne(*Argumente)` liefert das Ergebnis
    (aus dem Zwischenspeicher oder frisch gerechnet). Rückgabe: die Ergebnisse in der Reihenfolge der Schritte."""
    n = len(schritte)
    ergebnisse = []
    with st.status(titel, expanded=True) as status:
        balken = st.progress(0.0, text=f"0 von {n} fertig")
        for i, (beschriftung, args) in enumerate(schritte):
            balken.progress(i / n, text=f"{beschriftung} (Schritt {i + 1} von {n})")
            ergebnisse.append(rechne(*args))
        balken.progress(1.0, text=f"{n} von {n} fertig")
        status.update(label=f"{titel}: fertig", state="complete", expanded=False)
    return ergebnisse


def _zusammen(ergebnisse: list):
    laeufe = {s: lauf for s, (lauf, _) in zip(C.STUFEN, ergebnisse)}
    return laeufe, sum(sek for _, sek in ergebnisse)


def rotation(ordnung: int, luecken: int, seed: int, budget: int):
    """Die drei Stärken auf der Einzelinstanz mit Fortschrittsanzeige (je Stärke ein Schritt). Rückgabe: (Läufe je Stärke, Rechenzeit der Anzeige)."""
    schritte = [(f"Stärke {C.STUFEN_NAMEN[s]}", (ordnung, luecken, seed, budget, s)) for s in C.STUFEN]
    return _zusammen(mit_fortschritt(f"Rechne Ordnung {ordnung}, bis zu {E.zahl(budget)} Knoten je Stärke", schritte, rotation_stufe))


def rotation_aus_speicher(ordnung: int, luecken: int, seed: int, budget: int):
    """Wie `rotation`, ohne Anzeige (aus dem Zwischenspeicher; rechnet nur, was dort fehlt)."""
    return _zusammen([rotation_stufe(ordnung, luecken, seed, budget, s) for s in C.STUFEN])
