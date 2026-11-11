"""AllDifferent – das Mengenargument - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Ein Mini-CP mit der Bedingung „alle verschieden“ in drei Stärken (paarweise, Bounds über Hall-Intervalle, Régin per Matching), vier Experimente.
Aufwand wird in Knoten, Fehlschlägen, Propagationsaufrufen und Grundoperationen gezählt, nie in Sekunden.

Lauffähig mit: streamlit run app.py
"""

import time

import pandas as pd
import streamlit as st

import ald_constants as C
import ald_evaluation as E
import ald_scenario as S
import ald_search as Q
import ald_visualization as V
from ald_layout import dunkles_design, kopf_css
from ald_presets import (
    SETTING_SPECS,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="AllDifferent – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _wurzel(beispiel, eigene):
    inst = E.beispiel_instanz(beispiel, eigene)
    return inst, E.wurzel_tabelle(inst)


@st.cache_data(show_spinner=False)
def _kern_h1():
    inst = S.h1_hall()
    return {st: E.messung(Q.loese(inst.dom_liste(), inst.gruppen, st)) for st in C.STUFEN}


@st.cache_data(show_spinner=False)
def _hall(k, m, frei, budget):
    t0 = time.perf_counter()
    zeilen = E.hall_zeilen(k, m, frei, budget)
    return zeilen, time.perf_counter() - t0


@st.cache_data(show_spinner=False)
def _rotation(ordnung, luecken, seed, budget):
    t0 = time.perf_counter()
    laeufe = E.rotationsplan_laeufe(ordnung, luecken, seed, budget)
    return laeufe, time.perf_counter() - t0


@st.cache_data(show_spinner=False)
def _sweep():
    return E.lade_sweep()


@st.cache_data(show_spinner=False)
def _rotation_domaenen(ordnung, luecken, seed, stufe):
    inst, _ = S.rotationsplan_instanz(ordnung, luecken, seed)
    ok, dom, _, _ = Q.wurzel_propagation(inst.dom_liste(), inst.gruppen, stufe)
    return inst, ok, [set(d) for d in dom]


def _stufe_name(s):
    return C.STUFEN_NAMEN[s]


def _delta(knoten: int, referenz: int) -> dict:
    """Delta „mein Wert minus Referenz“ (A); Farbe regelt delta_color="inverse", bei Gleichstand grau ohne Pfeil."""
    if knoten == referenz:
        return dict(delta="gleich wie A", delta_color="off")
    return dict(delta=f"{knoten - referenz:+d} gegen A", delta_color="inverse")


def _tabelle(daten: dict, spalten: list):
    st.dataframe(pd.DataFrame(daten, columns=spalten), hide_index=True, width="stretch")


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in ald_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧩 AllDifferent – das Mengenargument")
st.markdown(
    """
**Wer „alle verschieden“ nur als Paare prüft, übersieht, dass vier Aufgaben nicht auf drei Werte passen.** Ein **Mengenargument (Hall)** oder ein **Matching (Régin)**
erkennt das an der Wurzel (ein Knoten); die paarweise Suche braucht dafür bei sieben Variablen auf sechs Werte 1 237 Knoten. Die Demo baut ein kleines Constraint-Programming-Programm
mit der Bedingung AllDifferent in **drei Stärken** und misst den Aufwand in **Knoten, Fehlschlägen, Propagationsaufrufen und Grundoperationen**, nie in Sekunden.

Weiter unten: vier Experimente (Reiter), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert AllDifferent", expanded=True):
    st.markdown(
        """
Eine **Gruppe** von Variablen soll paarweise verschiedene Werte bekommen (hier: jede Zeile und jede Spalte eines Rotationsplans). Die Suche wählt eine Variable,
probiert einen Wert und **propagiert**: Sie streicht Werte aus den Domänen der übrigen Variablen, die nie zu einer Lösung führen können. Wie viel gestrichen wird, hängt von der Stärke:

| Stärke | Was sie sieht | Was sie nicht sieht | Grundoperationen je Aufruf (Median je Zelle des vorgerechneten Sweeps, Ordnung 10 bis 15) |
|---|---|---|---|
| **A – paarweise** | Ist eine Variable festgelegt, fällt ihr Wert aus allen anderen Domänen. | Dass k + 1 Variablen nicht auf k Werte passen. | etwa 80 bis 240 |
| **B – Bounds** | Hall-Intervalle: Liegen so viele Variablen in einem Wertebereich [a, b], wie er Werte hat, gehören die Werte ihnen, und die Schranken der anderen springen heraus. | Löcher in den Domänen: nur kleinster und größter Wert wandern. | etwa 470 bis 1 800 (das 5,7- bis 8,9-Fache von A; einfache kubische Fassung) |
| **C – Régin** | Maximales Matching Variablen–Werte plus Kreise und Wechselwege: jeder Wert, der in keiner vollständigen verschiedenen Belegung vorkommt, fällt weg (Bereichskonsistenz). | – | etwa 115 bis 260 (das 0,87- bis 1,63-Fache von A) |

C enthält A und B: nach der Wurzelpropagation gilt Domäne C ⊆ Domäne B ⊆ Domäne A. Ein **Knoten** ist jeder Zustand der Suche nach Propagation (Wurzel, jeder Zweig und jeder Lösungsknoten).
        """
    )

load_permalink_settings()
init_session_state_defaults()
st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Stärke und Rechenbudget**")
    stufe = st.selectbox("Stärke für die Schritt-Ansicht", C.STUFEN, format_func=_stufe_name, key="stufe_select",
                         help="Gilt für die Schritt-für-Schritt-Ansicht und das Gitter im Reiter „Rotationsplan mit Lücken“; die Vergleiche zeigen immer alle drei Stärken.")
    budget = st.select_slider("Knotenbudget", options=C.BUDGET_OPTIONEN, key="budget_slider",
                              help="Nach so vielen Knoten bricht eine Suche ab; das Ergebnis heißt dann „mindestens“ so viele Knoten.")
    st.markdown("**Zufall**")
    seed = st.number_input("Zufalls-Seed des Rotationsplans", *bounds("seed_input"), key="seed_input", step=1,
                           help="Bestimmt das Lösungsquadrat und die Vorbelegung (SplitMix64). Gilt im Reiter „Rotationsplan mit Lücken“.")
    st.button("🎲 Neuer Zufalls-Seed", width="stretch", on_click=randomize_seed)

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was sieht das Mengenargument, das die paarweise Prüfung nicht sieht?")
h1 = _kern_h1()
c1, c2, c3 = st.columns(3)
c1.metric("A – paarweise: Knoten", E.zahl(h1["A"].knoten), delta="Referenz", delta_color="off")
c2.metric("B – Bounds: Knoten", E.zahl(h1["B"].knoten), **_delta(h1["B"].knoten, h1["A"].knoten))
c3.metric("C – Régin: Knoten", E.zahl(h1["C"].knoten), **_delta(h1["C"].knoten, h1["A"].knoten))
kind, text = E.verdict_kern(h1)
getattr(st, kind)(text)
st.caption("Handbeispiel H1 (von Hand nachgerechnet, in den Tests): a1 bis a4 mit Werten {1, 2, 3} und vier freie Variablen f1 bis f4 mit Werten {1, 2}, die in keiner Bedingung stehen.")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🔬 Eine Gruppe von Hand", "🔬 Hall-Verletzung wächst", "🔬 Rotationsplan mit Lücken", "🔬 Kosten je Aufruf"])

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

with tab1:
    st.subheader("🔬 Eine Gruppe von Hand: Schluss für Schluss")
    st.caption("Das Beispiel wählen, die Stärke steht in der Seitenleiste. Jeder Schluss der Propagation an der Wurzel ist ein Schritt; die Matrix zeigt die Domänen nach dem gewählten Schritt.")
    beispiel = st.selectbox("Beispiel", C.BEISPIELE, key="beispiel_select")
    eigene = C.EIGENE_STANDARD
    fehler = None
    if beispiel == C.BEISPIEL_EIGEN:     # das Textfeld erscheint nur hier: kein Regler, der in anderen Einstellungen wirkungslos wäre
        eigene = st.text_input("Eigene Domänen (Variablen mit Semikolon trennen, Werte mit Leerzeichen)", key="eigene_input", max_chars=C.TEXT_MAX,
                               help=f"Zum Beispiel „1 3; 1 3; 1 2 3; 2 3 4“. {C.EIGENE_VAR_MIN} bis {C.EIGENE_VAR_MAX} Variablen, Werte {C.EIGENE_WERT_MIN} bis {C.EIGENE_WERT_MAX}.")
        try:
            E.parse_domaenen(eigene)
        except ValueError as ex:
            fehler = str(ex)
    if fehler:
        st.error(fehler)
    else:
        inst, tabelle = _wurzel(beispiel, eigene)
        kind, text = E.verdict_wurzel(tabelle, inst.n)
        getattr(st, kind)(text)
        zeilen = [[C.STUFEN_NAMEN[s], "ja" if tabelle[s].ok else "Widerspruch", tabelle[s].festgelegt, tabelle[s].gestrichen, tabelle[s].aufrufe, tabelle[s].ops] for s in C.STUFEN]
        _tabelle(list(map(list, zeilen)), ["Stärke", "Wurzel ohne Widerspruch", "Variablen festgelegt", "Werte gestrichen", "Propagationsaufrufe", "Grundoperationen"])
        spur = list(tabelle[stufe].spur)
        st.markdown(f"**Schritt für Schritt, Stärke {C.STUFEN_NAMEN[stufe]}** ({len(spur)} {'Schluss' if len(spur) == 1 else 'Schlüsse'})")
        if not spur:
            st.info("Diese Stärke zieht an der Wurzel keinen Schluss: nichts wird gestrichen.")
            schritt = 0
        else:
            schritt = st.slider("Schritt", 0, len(spur), 0, key=f"schritt_{beispiel}_{stufe}_{len(spur)}_{eigene}",
                                help="0 = Ausgangszustand; jeder Schritt wendet einen weiteren Schluss an.")
        vorher = E.domaenen_nach_schritt(inst, spur, max(0, schritt - 1))
        nachher = E.domaenen_nach_schritt(inst, spur, schritt)
        links, rechts = st.columns([3, 2])
        with links:
            if inst.ordnung:
                st.plotly_chart(V.build_grid(inst.ordnung, inst.namen, nachher), width="stretch", key="grid_hand")
                st.caption("Grün: Zelle festgelegt. Grau: die Schichten, die in der Zelle noch möglich sind.")
            else:
                st.plotly_chart(V.build_matrix(inst, vorher, nachher), width="stretch", key="matrix_hand")
                st.caption("Hellgrün: Wert in der Domäne. Rot ✗: in diesem Schritt gestrichen. Dunkelgrün ✓: Variable festgelegt. Grau: Wert nie in der Domäne.")
        with rechts:
            if schritt >= 1:
                st.markdown(f"**Schritt {schritt}:** " + E.schritt_text(inst, spur[schritt - 1]))
            elif spur:
                st.markdown("**Ausgangszustand.** Mit dem Regler „Schritt“ die Schlüsse einzeln anwenden.")
            if spur:
                with st.expander("Alle Schlüsse im Überblick"):
                    for i, e in enumerate(spur, 1):
                        st.markdown(f"{i}. {E.schritt_text(inst, e)}")
        if len(inst.gruppen) == 1:
            with st.expander("🕸️ Matching-Graph (Régin) für den gewählten Schritt", expanded=False):
                fig, groesse, p = V.build_matching(inst, nachher)
                st.plotly_chart(fig, width="stretch", key="matching_hand")
                if groesse < p:
                    st.warning(f"Das größte Matching hat nur {groesse} Kanten bei {p} Variablen: es gibt keine vollständige verschiedene Belegung (Hall-Verletzung).")
                st.caption("Dick grün: Kopplungskante des Matchings. Rot gestrichelt: Kante, die in keinem maximalen Matching liegt (Régin streicht sie). "
                           "Grau: Domänenkante, die bleibt. Gleiche Knotenfarbe: dieselbe starke Zusammenhangskomponente (grau: Komponente aus einem Knoten).")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

with tab2:
    st.subheader("🔬 Hall-Verletzung wächst: k + 1 Variablen auf k Werten")
    st.caption("Die Aufgabe ist unlösbar (Schubfachprinzip). Gemessen wird, nach wie vielen Knoten die Suche das merkt. Optional stehen m freie Variablen davor, die in keiner Bedingung vorkommen.")
    ca, cb, cc = st.columns(3)
    hall_k = ca.slider("k (größte Zeile der Tabelle)", *bounds("hall_k_slider"), key="hall_k_slider", help="Die Tabelle zeigt alle k von 3 bis zu diesem Wert.")
    hall_m = cb.slider("freie Variablen m", *bounds("hall_m_slider"), key="hall_m_slider", help="Variablen, die in keiner AllDifferent-Gruppe stehen und zuerst belegt werden (kleinere Domäne).")
    hall_frei = cc.radio("Werte je freier Variable", C.HALL_FREI_OPTIONEN, key="hall_frei_radio", horizontal=True)
    auto = hall_m == 0 and hall_k <= 7
    schluessel = (hall_k, hall_m, hall_frei, budget)
    if not auto:
        st.caption(f"Mit freien Variablen oder k > 7 kann die paarweise Suche bis zum Budget ({E.zahl(budget)} Knoten) rechnen; das dauert je Zeile einige Sekunden, deshalb startet die Rechnung erst auf Knopfdruck.")
        if st.button("▶ Tabelle rechnen", key="hall_rechnen"):
            with st.spinner(f"Rechne k = 3 bis {hall_k}, je Stärke bis zu {E.zahl(budget)} Knoten …"):
                st.session_state["hall_ergebnis"] = (schluessel, *_hall(*schluessel))
    else:
        with st.spinner("Rechne …"):
            st.session_state["hall_ergebnis"] = (schluessel, *_hall(*schluessel))
    erg = st.session_state.get("hall_ergebnis")
    if erg is None or erg[0] != schluessel:
        st.info("Für diese Einstellung ist noch nichts gerechnet. Mit „Tabelle rechnen“ starten.")
    else:
        _, zeilen_h, sekunden = erg
        kind, text = E.verdict_hall(zeilen_h, hall_m)
        getattr(st, kind)(text)
        rows = [[z["k"], E.knoten_text(z["A"]), E.knoten_text(z["B"]), E.knoten_text(z["C"]), E.vormessung_text(z["k"], hall_m, hall_frei), z["A"].aufrufe] for z in zeilen_h]
        _tabelle(rows, ["k", "A paarweise: Knoten", "B Bounds: Knoten", "C Régin: Knoten", "Vormessung A (zur Kontrolle)", "A: Propagationsaufrufe"])
        st.plotly_chart(V.build_hall(zeilen_h), width="stretch", key="hall_chart")
        st.caption(f"Hohle Punkte: Abbruch am Budget von {E.zahl(budget)} Knoten (die Zahl ist eine Untergrenze). Rechenzeit dieser Tabelle: {sekunden:.1f} s (nur Anzeige, kein Befund). "
                   "Die Vergleichsspalte stammt aus der Vormessung der Planung (Rohdatei `out_cp_v10_hall.txt`, Mini-CP der Phase 0) und gilt nur bei freien Variablen mit drei Werten und m = 0 oder 3.")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

with tab3:
    st.subheader("🔬 Rotationsplan mit Lücken")
    st.caption("Mitarbeiter mal Tage, jede Schicht je Zeile und je Spalte genau einmal; ein Teil der Zellen ist vorbelegt, die Aufgabe ist nach Konstruktion erfüllbar. "
               "Der Zufalls-Seed steht in der Seitenleiste.")
    cx, cy = st.columns(2)
    ordnung = cx.slider("Ordnung (Mitarbeiter = Tage = Schichten)", *bounds("ordnung_slider"), key="ordnung_slider")
    luecken = cy.slider("Lücken in Prozent der Zellen", *bounds("lueck_slider"), key="lueck_slider", help="Der Rest ist vorbelegt, ganzzahlig auf die nächste Zelle gerundet.")
    with st.spinner(f"Rechne Ordnung {ordnung}, bis zu {E.zahl(budget)} Knoten je Stärke …"):
        laeufe, sek_einzel = _rotation(ordnung, luecken, int(seed), budget)
    mess = {s: E.messung(laeufe[s]) for s in C.STUFEN}
    st.markdown("**Einzelinstanz (live gerechnet)**")
    m1, m2, m3 = st.columns(3)
    for col, s in zip((m1, m2, m3), C.STUFEN):
        col.metric(f"{C.STUFEN_KURZ[s]}: Knoten", E.knoten_text(mess[s]).replace("mindestens ", "≥ ").replace(" (Budget erreicht)", ""),
                   **({} if s == "A" else _delta(mess[s].knoten, mess["A"].knoten)))
    kind, text = E.verdict_einzel(mess, ordnung, luecken)
    getattr(st, kind)(text)
    _tabelle([[C.STUFEN_NAMEN[s], E.knoten_text(mess[s]), mess[s].fehlschlaege, mess[s].aufrufe, mess[s].festgelegt] for s in C.STUFEN],
             ["Stärke", "Knoten", "Fehlschläge", "Propagationsaufrufe", f"festgelegte Zellen nach der Wurzel (von {ordnung * ordnung})"])
    if ordnung <= 8:
        inst_r, ok_r, dom_r = _rotation_domaenen(ordnung, luecken, int(seed), stufe)
        st.plotly_chart(V.build_grid(ordnung, inst_r.namen, dom_r), width="stretch", key="grid_rotation")
        st.caption(f"Gitter nach der Wurzelpropagation, Stärke {C.STUFEN_NAMEN[stufe]}. Rechenzeit der Einzelinstanz: {sek_einzel:.1f} s (nur Anzeige, kein Befund).")
    else:
        st.caption(f"Das Gitter erscheint bis Ordnung 8. Rechenzeit der Einzelinstanz: {sek_einzel:.1f} s (nur Anzeige, kein Befund).")

    st.markdown("**Vorgerechneter Sweep über 20 feste Zufalls-Seeds (nicht live)**")
    sweep = _sweep()
    meta = sweep["meta"]
    st.caption(f"Vorgerechnet mit `{meta['skript']}` (Seeds 0 bis 19, Knotenbudget {E.zahl(meta['knotenbudget'])}, nur erfüllbare Instanzen, Gegenprobe: {meta['gegenprobe']}); "
               "unabhängig vom Zufalls-Seed und vom Knotenbudget der Seitenleiste.")
    vert = E.zellen_verteilung(sweep, ordnung, luecken)
    if vert is None:
        st.info(f"Für Ordnung {ordnung} mit {luecken} % Lücken ist kein Sweep vorgerechnet; die Tabelle darunter zeigt die vorgerechneten Zellen.")
    else:
        kind, text = E.verdict_verteilung(vert, ordnung, luecken)
        getattr(st, kind)(text)
        zelle = E.sweep_zelle(sweep, ordnung, luecken)
        st.plotly_chart(V.build_ecdf(zelle["stufen"], meta["knotenbudget"]), width="stretch", key="ecdf")
        _tabelle([[C.STUFEN_NAMEN[s], E.zahl(int(vert[s]["median"])) if float(vert[s]["median"]).is_integer() else E.dezimal(vert[s]["median"]), E.zahl(vert[s]["p90"]), E.zahl(vert[s]["max"]),
                   f"{vert[s]['abbrueche']} von {vert[s]['n']}"] for s in C.STUFEN if s in vert], ["Stärke", "Median", "90-Prozent-Rang", "Maximum", "Abbrüche am Budget"])
    alle = []
    for z in sweep["zellen"]:
        v = E.zellen_verteilung(sweep, z["ordnung"], z["luecken"])
        alle.append([z["ordnung"], z["luecken"]] + [E.zahl(int(v[s]["median"])) if s in v else "–" for s in C.STUFEN] + [E.zahl(v[s]["max"]) if s in v else "–" for s in C.STUFEN]
                    + [str(v[s]["abbrueche"]) if s in v else "–" for s in C.STUFEN])
    with st.expander("Alle vorgerechneten Zellen (Median, Maximum, Abbrüche je Stärke)"):
        _tabelle(alle, ["Ordnung", "Lücken %", "Median A", "Median B", "Median C", "Max A", "Max B", "Max C", "Abbrüche A", "Abbrüche B", "Abbrüche C"])
        st.caption("Bei Ordnung 15 und 35, 40, 45 % Lücken sind nur A und C gerechnet. Ein Strich bedeutet: nicht gerechnet. Median ganzzahlig gerundet angezeigt.")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

with tab4:
    st.subheader("🔬 Kosten je Aufruf: was Régin kostet")
    st.markdown(
        "Ein Régin-Aufruf kostet mehr als eine paarweise Prüfung: **Aufrufzahlen allein täuschen.** Deshalb zählt dieser Reiter **Grundoperationen**: "
        "ein Zugriff auf eine Domäne (Länge, Minimum, Maximum, Mitgliedschaft, Streichen) oder ein besuchter Kantenzug im Variablen-Werte-Graphen (Matching-Suche, Graphaufbau, Tarjan, Erreichbarkeit, Prüfung). "
        "Gesamtkosten = Summe der Grundoperationen über alle Aufrufe der Suche."
    )
    st.markdown("**Einzelinstanz aus dem Reiter „Rotationsplan mit Lücken“**")
    ops_dict = {s: laeufe[s].ops for s in C.STUFEN}
    _tabelle([[C.STUFEN_NAMEN[s], E.zahl(laeufe[s].ops_dom), E.zahl(laeufe[s].ops_kanten), E.zahl(laeufe[s].ops), E.zahl(laeufe[s].aufrufe), E.zahl(round(mess[s].ops_je_aufruf))] for s in C.STUFEN],
             ["Stärke", "Domänenzugriffe", "Kantenbesuche", "Grundoperationen gesamt", "Propagationsaufrufe", "Grundoperationen je Aufruf"])
    kind, text = E.verdict_kosten(mess)
    getattr(st, kind)(text)
    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(V.build_balken({s: mess[s].ops_je_aufruf for s in C.STUFEN}, "Grundoperationen je Aufruf"), width="stretch", key="kosten_je_aufruf")
    with col_b:
        st.plotly_chart(V.build_balken(ops_dict, "Grundoperationen gesamt (logarithmisch)", log=True), width="stretch", key="kosten_gesamt")
    if any(mess[s].abgebrochen for s in C.STUFEN):
        st.caption("Mindestens eine Stärke brach am Budget ab: ihre Summen sind Untergrenzen.")
    st.markdown("**Mediane des vorgerechneten Sweeps** (dieselbe Zelle wie im Reiter „Rotationsplan mit Lücken“, falls vorgerechnet)")
    if vert is None:
        st.info("Für die gewählte Ordnung und die gewählten Lücken ist kein Sweep vorgerechnet.")
    else:
        kosten = E.kosten_aus_verteilung(vert)
        _tabelle([[C.STUFEN_NAMEN[s], E.zahl(kosten[s].knoten), E.zahl(kosten[s].aufrufe), E.zahl(kosten[s].ops), E.zahl(round(vert[s]["ops_je_aufruf_median"]))] for s in C.STUFEN if s in kosten],
                 ["Stärke", "Knoten (Median)", "Propagationsaufrufe (Median)", "Grundoperationen (Median)", "Grundoperationen je Aufruf (Median der Läufe)"])
        kind, text = E.verdict_kosten(kosten)
        getattr(st, kind)(text)
        st.caption("Verglichen werden Mediane je Größe; das Verhältnis der Mediane ist nicht der Median der Verhältnisse.")
    st.caption("Die Kosten hängen an dieser Umsetzung: das Matching wird bei jedem Aufruf neu berechnet (nicht aus dem Vorgänger fortgeführt), und die Bounds-Stufe prüft alle Intervalle einfach durch (kubisch in der Gruppengröße).")

sync_query_params({k: st.session_state.get(k, spec.default) for k, spec in SETTING_SPECS.items()})

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Die Rotationspläne sind erfüllbar** (aus einem vollständigen Quadrat gezogen) | Unerfüllbarkeit ist nur an der Hall-Instanz gemessen; wie sich die Stärken auf unerfüllbaren Rotationsplänen verhalten, zeigt die Demo nicht. |
| **Variablenwahl und Werteordnung sind fest** (kleinste Domäne, kleinster Wert zuerst) | Eine andere Wahl, etwa nach Fehlschlägen gewichtet, wurde nicht gemessen und könnte die paarweise Suche verbessern. |
| **Die Kosten gelten für diese Umsetzung** | Matching bei jedem Aufruf neu, einfache kubische Bounds-Prüfung: die Grundoperationen sind Eigenschaften dieser Fassung, nicht der Verfahren der Literatur. |
| **Ein Erzeuger, 20 Zufalls-Seeds je Zelle** | Die Lage der schwersten Lücken-Region ist bei so wenigen Instanzen nicht gesichert; die Demo behauptet sie nicht. |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben und gesucht.** Gegeben sind Variablen $x_1, \dots, x_p$ mit endlichen Domänen $D_1, \dots, D_p \subset \mathbb{Z}$ und eine Gruppe, in der alle Werte verschieden sein müssen. Gesucht ist eine Belegung $x_i \in D_i$ mit $x_i \neq x_j$ für $i \neq j$ in jeder Gruppe, oder der Beweis, dass es keine gibt.

| Symbol | Bedeutung |
|---|---|
| $x_i$, $D_i$ | Variable $i$ und ihre Domäne |
| $p$ | Zahl der Variablen einer Gruppe |
| $I$ | eine Menge von Werten (bei Bounds ein Intervall $[a, b]$) |
| $G$ | Wertegraph: Variablen und Werte als Knoten, Kante $(x_i, v)$ für $v \in D_i$ |

**Hall-Bedingung (Schubfachprinzip).** Eine Gruppe hat nur dann eine Lösung, wenn für jede Wertemenge $I$ gilt:

$$|\{\, i : D_i \subseteq I \,\}| \;\le\; |I|.$$

Liegt für ein $I$ Gleichheit vor, belegen diese Variablen alle Werte von $I$ (eine Hall-Menge), und $I$ fällt aus den Domänen aller übrigen Variablen. Die Bedingung ist auch hinreichend (Satz von Hall für das Matching der Variablen auf Werte).

**Stufe B (Bounds, eigene Fassung).** Die Bedingung wird nur für Intervalle geprüft, deren Grenzen Minimum und Maximum von Domänen sind:

$$|\{\, i : [\min D_i, \max D_i] \subseteq [a, b] \,\}| \;\le\; b - a + 1 \quad \text{für alle } a \le b.$$

Bei Gleichheit springen Minimum und Maximum der übrigen Variablen aus $[a, b]$; Löcher in den Domänen bleiben unbeachtet.

**Stufe C (Bereichskonsistenz nach Régin).** Ein Wert $v \in D_i$ bleibt genau dann, wenn die Kante $(x_i, v)$ in einem Matching von $G$ liegt, das alle Variablen überdeckt. Verfahren: ein maximales Matching $M$ bestimmen (hat es weniger als $p$ Kanten, gibt es keine Lösung); Kopplungskanten von der Variablen zum Wert, alle anderen Kanten vom Wert zur Variablen ausrichten; eine Kante außerhalb von $M$ bleibt, wenn ihre Enden in derselben starken Zusammenhangskomponente liegen (Wechselkreis) oder ihr Wert von einem freien Wert aus erreichbar ist (Wechselweg). Alle übrigen Kanten werden gestrichen. Régin gibt für das Gesamtverfahren $O(p^2 d^2)$ an ($d$ = größte Domäne, Matching nach Hopcroft–Karp); diese Demo nutzt einfache Erweiterungspfade.

**Aufwand.** Ein *Knoten* ist ein Zustand der Suche nach Propagation (die Wurzel eingeschlossen). Ein *Fehlschlag* ist ein Knoten mit Widerspruch. Eine *Grundoperation* ist ein Domänenzugriff oder ein besuchter Kantenzug im Wertegraphen.

**Literatur.** J.-C. Régin: A filtering algorithm for constraints of difference in CSPs. AAAI 1994 (Volltext gelesen). C. P. Gomes, B. Selman: Problem structure in the presence of perturbations. AAAI 1997 (zufällig vorbelegte Quadrate, Spitze der Kosten bei etwa 42 % Vorbelegung; die Rotationspläne dieser Demo entstehen anders, aus einem vollständigen Quadrat, und sind eine andere Familie). Die Bounds-Stufe ist eine eigene Fassung; eine Quelle dafür wurde nicht gelesen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html)."
)
