"""Messskript: Sweep über 20 feste Zufalls-Seeds für den Rotationsplan, schreibt `ald_sweep_vorgerechnet.json` (Stand des Baus).

Aufruf (Wurzelordner des Repos):  python tools/messung_sweep.py [--gegenprobe] [--out ald_sweep_vorgerechnet.json]

Je Zelle (Ordnung, Lückenanteil in Prozent) und Stärke (A, B, C) werden die Seeds 0 bis 19 gelöst (Erzeuger `ald_scenario.rotationsplan_instanz`,
SplitMix64, Knotenbudget 20 000). Gespeichert wird je Lauf: Knoten, Fehlschläge, Propagationsaufrufe, Grundoperationen (Domänenzugriffe und
Kantenbesuche), Abbruch am Budget, Zahl der nach der Wurzel festgelegten Zellen. Sekunden werden nicht gespeichert.
Mit `--gegenprobe` wird jede Antwort gegen den unabhängigen Prüfer `ist_loesung` und gegen OR-Tools CP-SAT geprüft (nur im Test-venv,
`ortools` steht in requirements-dev.txt, nie in der App); die Zahl der Abweichungen steht im Kopf der Datei.
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ald_scenario as S  # noqa: E402
import ald_search as Q  # noqa: E402

SEEDS = tuple(range(20))
BUDGET = 20000
ZELLEN = [(o, p, "ABC") for o in (10, 12, 14, 15) for p in (50, 55, 58, 62)] + [(15, p, "AC") for p in (35, 40, 45)]


def cpsat_erfuellbar(inst):
    from ortools.sat.python import cp_model

    m = cp_model.CpModel()
    x = [m.NewIntVarFromDomain(cp_model.Domain.FromValues(sorted(d)), f"x{i}") for i, d in enumerate(inst.doms)]
    for g in inst.gruppen:
        m.AddAllDifferent([x[i] for i in g])
    s = cp_model.CpSolver()
    s.parameters.num_workers = 1
    s.parameters.max_time_in_seconds = 60
    return s.Solve(m) in (cp_model.OPTIMAL, cp_model.FEASIBLE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gegenprobe", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "ald_sweep_vorgerechnet.json"))
    args = ap.parse_args()
    abweichungen = 0
    zellen = []
    t0 = time.time()
    for ordnung, prozent, stufen in ZELLEN:
        zelle = {"ordnung": ordnung, "luecken": prozent, "stufen": {}}
        for seed in SEEDS:
            inst, _ = S.rotationsplan_instanz(ordnung, prozent, seed)
            if args.gegenprobe and not cpsat_erfuellbar(inst):
                abweichungen += 1
            for st in stufen:
                lauf = Q.loese(inst.dom_liste(), inst.gruppen, st, budget=BUDGET)
                if args.gegenprobe and lauf.antwort != "abgebrochen" and not (lauf.antwort == "loesbar" and S.ist_loesung(inst, lauf.loesung)):
                    abweichungen += 1
                zelle["stufen"].setdefault(st, []).append({
                    "seed": seed, "knoten": lauf.knoten, "fehlschlaege": lauf.fehlschlaege, "aufrufe": lauf.aufrufe,
                    "ops_dom": lauf.ops_dom, "ops_kanten": lauf.ops_kanten, "abgebrochen": lauf.antwort == "abgebrochen",
                    "festgelegt_wurzel": lauf.festgelegt_wurzel,
                })
        zellen.append(zelle)
        print(f"Ordnung {ordnung}, Lücken {prozent} %: fertig ({time.time() - t0:.0f} s Lauf, kein Befund)", flush=True)
    daten = {
        "meta": {
            "erzeuger": "ald_scenario.rotationsplan_instanz (SplitMix64, Zyklentausch, Vorbelegung zufällig aus dem Lösungsquadrat)",
            "seeds": list(SEEDS), "knotenbudget": BUDGET, "stufen": "A paarweise, B plus Bounds (Hall-Intervalle), C Régin",
            "nur_erfuellbar": True, "skript": "tools/messung_sweep.py",
            "gegenprobe": ("CP-SAT und Lösungsprüfer, Abweichungen: %d" % abweichungen) if args.gegenprobe else "nicht ausgeführt",
        },
        "zellen": zellen,
    }
    Path(args.out).write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    print("Abweichungen gegen CP-SAT und Prüfer:", abweichungen if args.gegenprobe else "(nicht geprüft)")


if __name__ == "__main__":
    main()
