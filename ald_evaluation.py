"""Kennzahlen, Verdikt-Logik und Auswertung der vier Experimente. Verdikte sind reine Funktionen (Art, Text) auf Zahlen, nie auf Seeds."""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import median

import ald_constants as C
import ald_scenario as S
import ald_search as Q
from ald_algorithm import beschreibe

SWEEP_PFAD = Path(__file__).resolve().parent / C.SWEEP_DATEI


@dataclass(frozen=True)
class Settings:
    stufe: str = C.DEFAULT_STUFE
    seed: int = C.DEFAULT_SEED
    budget: int = C.DEFAULT_BUDGET
    beispiel: str = C.BEISPIEL_H2
    eigene: str = C.EIGENE_STANDARD
    hall_k: int = C.DEFAULT_HALL_K
    hall_m: int = C.DEFAULT_HALL_M
    hall_frei: int = C.DEFAULT_HALL_FREI
    ordnung: int = C.DEFAULT_ORDNUNG
    luecken: int = C.DEFAULT_LUECKE


@dataclass(frozen=True)
class Messung:
    """Zähler eines Suchlaufs (Knoten, Fehlschläge, Propagationsaufrufe, Grundoperationen) und ob er am Budget abbrach."""
    knoten: int
    fehlschlaege: int
    aufrufe: int
    ops: int
    abgebrochen: bool
    festgelegt: int | None = None

    @property
    def ops_je_aufruf(self) -> float:
        return self.ops / self.aufrufe if self.aufrufe else 0.0


def messung(lauf: Q.Lauf) -> Messung:
    return Messung(lauf.knoten, lauf.fehlschlaege, lauf.aufrufe, lauf.ops, lauf.antwort == "abgebrochen", lauf.festgelegt_wurzel)


def zahl(x: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner (deutsche Schreibweise, schmales festes Leerzeichen vermeiden: normales Leerzeichen)."""
    return f"{x:,}".replace(",", " ")


def dezimal(x: float, stellen: int = 1) -> str:
    return f"{x:,.{stellen}f}".replace(",", " ").replace(".", ",")


def knoten_text(m: Messung) -> str:
    return f"mindestens {zahl(m.knoten)} (Budget erreicht)" if m.abgebrochen else zahl(m.knoten)


# ------------------------------------------------------------------------------------------------------------------------------------
# Experiment 1: eine Gruppe von Hand
# ------------------------------------------------------------------------------------------------------------------------------------
def parse_domaenen(text: str) -> list:
    """„1 3; 1 3; 1 2 3“ -> [{1, 3}, {1, 3}, {1, 2, 3}]. Wirft ValueError mit einer deutschen Meldung bei ungültiger Eingabe."""
    teile = [t.strip() for t in text.split(";")]
    if any(not t for t in teile):
        raise ValueError("Jede Variable braucht mindestens einen Wert; Domänen mit Semikolon trennen, Werte mit Leerzeichen.")
    if not C.EIGENE_VAR_MIN <= len(teile) <= C.EIGENE_VAR_MAX:
        raise ValueError(f"Erlaubt sind {C.EIGENE_VAR_MIN} bis {C.EIGENE_VAR_MAX} Variablen, eingegeben wurden {len(teile)}.")
    doms = []
    for t in teile:
        try:
            werte = {int(w) for w in t.replace(",", " ").split()}
        except ValueError:
            raise ValueError(f"„{t}“ enthält etwas, das keine ganze Zahl ist.") from None
        if any(not C.EIGENE_WERT_MIN <= w <= C.EIGENE_WERT_MAX for w in werte):
            raise ValueError(f"Die Werte müssen zwischen {C.EIGENE_WERT_MIN} und {C.EIGENE_WERT_MAX} liegen („{t}“).")
        doms.append(werte)
    return doms


def beispiel_instanz(beispiel: str, eigene: str = C.EIGENE_STANDARD) -> S.Instanz:
    if beispiel == C.BEISPIEL_H1:
        return S.h1_hall()
    if beispiel == C.BEISPIEL_H3:
        return S.h3_rotationsplan()
    if beispiel == C.BEISPIEL_EIGEN:
        return S.aus_domaenen(parse_domaenen(eigene))
    return S.h2_loecher()


@dataclass(frozen=True)
class Wurzel:
    stufe: str
    ok: bool
    festgelegt: int
    gestrichen: int          # Zahl der gestrichenen (Variable, Wert)-Paare
    aufrufe: int
    ops: int
    domaenen: tuple          # je Variable ein sortiertes Tupel (bei Fehlschlag: Stand beim Widerspruch)
    spur: tuple


def wurzel_ergebnis(inst: S.Instanz, stufe: str) -> Wurzel:
    ok, dom, spur, z = Q.wurzel_propagation(inst.dom_liste(), inst.gruppen, stufe, spur=True)
    vorher = sum(len(d) for d in inst.doms)
    return Wurzel(stufe, ok, sum(1 for d in dom if len(d) == 1), vorher - sum(len(d) for d in dom), z.aufrufe, z.ops,
                  tuple(tuple(sorted(d)) for d in dom), tuple(spur))


def wurzel_tabelle(inst: S.Instanz) -> dict:
    return {st: wurzel_ergebnis(inst, st) for st in C.STUFEN}


def domaenen_nach_schritt(inst: S.Instanz, spur, schritt: int) -> list:
    """Domänen nach den ersten `schritt` Streichungen der Spur (Ereignisse ohne `werte` sind Fehlschläge und streichen nichts)."""
    dom = inst.dom_liste()
    for e in list(spur)[:schritt]:
        for w in e.get("werte", ()):
            dom[e["var"]].discard(w)
    return dom


def schritt_text(inst: S.Instanz, e: dict) -> str:
    text = beschreibe(e, lambda i: inst.namen[i])
    gruppe = e.get("gruppe")
    if gruppe is not None and len(inst.gruppen) > 1 and inst.gruppennamen:
        return f"({inst.gruppennamen[gruppe]}) {text}"
    return text


def verdict_wurzel(tabelle: dict, n: int) -> tuple[str, str]:
    """Verdikt des Reiters „Eine Gruppe von Hand“: wie viele Variablen jede Stärke an der Wurzel festlegt (oder dass sie scheitert)."""
    teile = []
    for st in C.STUFEN:
        w = tabelle[st]
        teile.append(f"{C.STUFEN_KURZ[st]}: " + (f"{w.festgelegt} von {n} Variablen festgelegt, {w.gestrichen} Werte gestrichen" if w.ok else "Widerspruch an der Wurzel"))
    satz = "Nach der Wurzelpropagation – " + "; ".join(teile) + "."
    ok = [tabelle[st].ok for st in C.STUFEN]
    if ok[0] and not ok[1] and not ok[2]:
        return "success", satz + " Die paarweise Prüfung merkt den Widerspruch nicht, das Mengenargument (Hall) und das Matching schon."
    werte = {(tabelle[st].ok, tabelle[st].festgelegt, tabelle[st].gestrichen) for st in C.STUFEN}
    if len(werte) == 1:
        return "info", satz + " Hier genügt die paarweise Prüfung: alle drei Stärken streichen dasselbe."
    return "success", satz


def verdict_kern(h1: dict) -> tuple[str, str]:
    """Kernfrage an der Hall-Instanz H1; `h1`: Stufe -> Messung."""
    a, b, c = h1["A"], h1["B"], h1["C"]
    satz = (f"Auf H1 (vier Variablen auf drei Werte, dazu vier freie Variablen) sieht die paarweise Suche den Fehlschlag erst nach {knoten_text(a)} Knoten ({a.fehlschlaege} Fehlschläge), "
            f"Bounds nach {knoten_text(b)} und Régin nach {knoten_text(c)}.")
    if a.knoten <= c.knoten:
        return "info", satz + " Hier genügt die paarweise Prüfung."
    return "success", satz + " Die Hall-Bedingung (vier Variablen, nur drei Werte) erkennt den Widerspruch an der Wurzel."


# ------------------------------------------------------------------------------------------------------------------------------------
# Experiment 2: Hall-Verletzung wächst
# ------------------------------------------------------------------------------------------------------------------------------------
def hall_zeilen(k_max: int, m: int, frei: int, budget: int) -> list:
    """Je k von HALL_K_MIN bis k_max: die Messungen der drei Stärken auf der Hall-Instanz (k + 1 Variablen auf k Werten, m freie Variablen)."""
    zeilen = []
    for k in range(C.HALL_K_MIN, k_max + 1):
        inst = S.hall_instanz(k, m, frei)
        zeilen.append({"k": k, **{st: messung(Q.loese(inst.dom_liste(), inst.gruppen, st, budget=budget)) for st in C.STUFEN}})
    return zeilen


def vormessung_text(k: int, m: int, frei: int) -> str:
    """Vergleichsspalte aus der Vormessung der Planung (nur bei freien Variablen mit drei Werten und m = 0 oder 3)."""
    if frei != 3 or (k, m) not in C.VORMESSUNG_HALL_A:
        return "–"
    w = C.VORMESSUNG_HALL_A[(k, m)]
    return f"mindestens {zahl(C.VORMESSUNG_BUDGET)}" if w is None else zahl(w)


def verdict_hall(zeilen: list, m: int) -> tuple[str, str]:
    z = zeilen[-1]
    a, b, c = z["A"], z["B"], z["C"]
    frei = "ohne freie Variablen" if m == 0 else f"mit {m} freien Variablen"
    satz = (f"Bei k = {z['k']} ({z['k'] + 1} Variablen auf {z['k']} Werte, {frei}) sieht die paarweise Suche den Fehlschlag erst nach {knoten_text(a)} Knoten, "
            f"Bounds nach {knoten_text(b)}, Régin nach {knoten_text(c)}.")
    ok_zeilen = [r for r in zeilen if not r["A"].abgebrochen]
    if len(ok_zeilen) >= 2 and ok_zeilen[-2]["A"].knoten > 0:
        v, w = ok_zeilen[-2], ok_zeilen[-1]
        satz += f" Von k = {v['k']} auf k = {w['k']} wächst A auf das {dezimal(w['A'].knoten / v['A'].knoten)}-fache."
    if a.knoten <= c.knoten:
        return "info", satz + " Hier genügt die paarweise Prüfung."
    return "success", satz


# ------------------------------------------------------------------------------------------------------------------------------------
# Experiment 3 und 4: Rotationsplan mit Lücken
# ------------------------------------------------------------------------------------------------------------------------------------
def rotationsplan_stufe(ordnung: int, luecken: int, seed: int, budget: int, stufe: str):
    """Eine Stärke auf der Einzelinstanz (eine Einheit von `rotationsplan_laeufe`)."""
    inst, _ = S.rotationsplan_instanz(ordnung, luecken, seed)
    return Q.loese(inst.dom_liste(), inst.gruppen, stufe, budget=budget)


def rotationsplan_laeufe(ordnung: int, luecken: int, seed: int, budget: int) -> dict:
    """Die drei Stärken auf einer Einzelinstanz (Ordnung, Lücken in Prozent, Zufalls-Seed)."""
    return {st: rotationsplan_stufe(ordnung, luecken, seed, budget, st) for st in C.STUFEN}


def verdict_einzel(m: dict, ordnung: int, luecken: int) -> tuple[str, str]:
    """Verdikt der Einzelinstanz; `m`: Stufe -> Messung."""
    a, b, c = m["A"], m["B"], m["C"]
    satz = (f"Ordnung {ordnung} mit {luecken} % Lücken: A braucht {knoten_text(a)} Knoten ({a.fehlschlaege} Fehlschläge), B {knoten_text(b)} ({b.fehlschlaege}), "
            f"C {knoten_text(c)} ({c.fehlschlaege}). Nach der Wurzel sind {a.festgelegt} (A), {b.festgelegt} (B) und {c.festgelegt} (C) von {ordnung * ordnung} Zellen festgelegt.")
    if a.knoten <= c.knoten and not a.abgebrochen:
        return "info", satz + " Auf dieser Instanz braucht die paarweise Suche nicht mehr Knoten als Régin: hier genügt die paarweise Prüfung."
    return "success", satz


def lade_sweep(pfad: Path = SWEEP_PFAD) -> dict:
    return json.loads(Path(pfad).read_text(encoding="utf-8"))


def sweep_zelle(daten: dict, ordnung: int, luecken: int):
    for z in daten["zellen"]:
        if z["ordnung"] == ordnung and z["luecken"] == luecken:
            return z
    return None


def perzentil(werte: list, anteil: float):
    """Nächster-Rang-Perzentil: der kleinste Wert, unter dem mindestens `anteil` der Werte liegen (Rang ceil(anteil * n))."""
    s = sorted(werte)
    return s[max(0, math.ceil(anteil * len(s)) - 1)]


def verteilung(zeilen: list, budget: int) -> dict:
    """Median, 90-Prozent-Rang, Maximum und Zahl der Abbrüche der Knoten über die Läufe einer Zelle; ein Abbruch zählt mit dem Budget (Untergrenze)."""
    knoten = [z["knoten"] for z in zeilen]
    ops_je = [(z["ops_dom"] + z["ops_kanten"]) / z["aufrufe"] for z in zeilen if z["aufrufe"]]
    return {
        "n": len(zeilen), "median": median(knoten), "p90": perzentil(knoten, 0.9), "max": max(knoten),
        "abbrueche": sum(1 for z in zeilen if z["abgebrochen"]), "budget": budget,
        "fehlschlaege_median": median(z["fehlschlaege"] for z in zeilen),
        "aufrufe_median": median(z["aufrufe"] for z in zeilen), "ops_median": median(z["ops_dom"] + z["ops_kanten"] for z in zeilen),
        "ops_je_aufruf_median": median(ops_je), "festgelegt_median": median(z["festgelegt_wurzel"] for z in zeilen if z["festgelegt_wurzel"] is not None),
    }


def zellen_verteilung(daten: dict, ordnung: int, luecken: int):
    """Verteilung je Stärke für eine vorgerechnete Zelle, sonst None."""
    z = sweep_zelle(daten, ordnung, luecken)
    if z is None:
        return None
    return {st: verteilung(zeilen, daten["meta"]["knotenbudget"]) for st, zeilen in z["stufen"].items()}


def _zahlmed(x: float) -> str:
    return dezimal(x, 0) if float(x).is_integer() else dezimal(x, 1)


def verdict_verteilung(v: dict, ordnung: int, luecken: int) -> tuple[str, str]:
    """Verdikt des Sweeps: Median gegen Schwanz (A gegen C). Schwellen: Median-Verhältnis ab 2 gilt als Unterschied im Median; als Schwanz zählt
    ein Abbruch mehr als bei C oder ein Maximum von mindestens dem Fünffachen."""
    a, c = v["A"], v["C"]
    n = a["n"]
    quot_med = a["median"] / c["median"] if c["median"] else float("inf")
    quot_max = a["max"] / c["max"] if c["max"] else float("inf")
    schwanz = a["abbrueche"] > c["abbrueche"] or quot_max >= 5
    abbr = ", ".join(f"{st}: {v[st]['abbrueche']}" for st in C.STUFEN if st in v)
    satz = (f"Ordnung {ordnung}, {luecken} % Lücken, {n} feste Zufalls-Seeds: Median {_zahlmed(a['median'])} Knoten bei A gegen {_zahlmed(c['median'])} bei C "
            f"(Verhältnis {dezimal(quot_med)}), Maximum {zahl(a['max'])} gegen {zahl(c['max'])}; Abbrüche am Budget von {zahl(a['budget'])} Knoten in {n} Läufen ({abbr}).")
    if quot_med < 2 and schwanz:
        return "success", satz + " Der Gewinn liegt im Schwanz, nicht im Median."
    if quot_med >= 2:
        return "success", satz + " Schon im Median braucht A mindestens doppelt so viele Knoten wie C."
    return "info", satz + " Hier genügt die paarweise Prüfung: Median-Verhältnis unter 2, Maximum-Verhältnis unter 5 und nicht mehr Abbrüche als bei C."


def verdict_kosten(m: dict) -> tuple[str, str]:
    """Verdikt der Kosten je Aufruf; `m`: Stufe -> Messung (Summen über einen Lauf oder Mediane einer Zelle).
    Aufrufzahlen allein täuschen: verglichen wird die Summe der Grundoperationen."""
    a, c = m["A"], m["C"]
    if min(a.knoten, c.knoten, a.aufrufe, c.aufrufe, a.ops, c.ops) <= 0:
        return "info", "Für dieses Verdikt fehlen Messwerte."
    knoten = a.knoten / c.knoten
    je = c.ops_je_aufruf / a.ops_je_aufruf
    gesamt = a.ops / c.ops
    mind = "mindestens " if a.abgebrochen else ""
    satz = (f"Régin braucht {mind}{dezimal(knoten)}-mal weniger Knoten als die paarweise Suche, kostet je Aufruf aber {dezimal(je)}-mal so viele Grundoperationen "
            f"({zahl(round(c.ops_je_aufruf))} gegen {zahl(round(a.ops_je_aufruf))}); ")
    if gesamt >= 1:
        satz += f"unterm Strich braucht Régin {mind}{dezimal(gesamt)}-mal weniger Grundoperationen."
        art = "success" if gesamt >= 1.25 else "info"
    else:
        satz += f"unterm Strich braucht Régin {dezimal(1 / gesamt)}-mal mehr Grundoperationen."
        art = "warning"
    satz += f" Insgesamt A {zahl(a.ops)}, C {zahl(c.ops)}"
    if "B" in m:
        b = m["B"]
        satz += f", zum Vergleich B {zahl(b.ops)} ({zahl(round(b.ops_je_aufruf))} je Aufruf)"
    return art, satz + " Grundoperationen."


def kosten_aus_verteilung(v: dict) -> dict:
    """Aus den Medianen einer Zelle Messungen für `verdict_kosten` bauen (Knoten, Aufrufe, Grundoperationen je Median)."""
    return {st: Messung(int(v[st]["median"]), int(v[st]["fehlschlaege_median"]), int(v[st]["aufrufe_median"]), int(v[st]["ops_median"]), v[st]["abbrueche"] > v[st]["n"] / 2)
            for st in v}
