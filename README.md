# AllDifferent – das Mengenargument – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-alldifferent-demo.streamlit.app/)**

Stück der **sat-constraint-programming**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, Wurzel des Arms „Constraint Programming“. Rückgriff ist [constraint-programming-demo](https://github.com/sebastian-hanisch/constraint-programming-demo) (Propagation am Rucksack), die weder „alle verschieden“ noch Mengenargumente kennt. Vehikel ist ein **Rotationsplan** (Mitarbeiter mal Tage, Schicht 1 bis n, jede Schicht je Zeile und je Spalte genau einmal, ein Teil der Zellen vorbelegt: ein lateinisches Quadrat mit Lücken) und eine **Hall-Instanz** (k + 1 Variablen auf k Werte). Das Constraint-Programming-Programm (Mini-CP) ist **neuer Code dieses Repos**; es hängt an keiner anderen Demo.

## Warum dieses Problem

**Wer „alle verschieden“ nur als Paare prüft, übersieht, dass vier Aufgaben nicht auf drei Werte passen.** Ein Mengenargument (Hall) oder ein Matching (Régin) erkennt das an der Wurzel, die paarweise Suche braucht dafür bei sieben Variablen auf sechs Werte 1 237 Knoten. Die Kernfrage der Demo: **Was sieht ein Mengenargument, das die paarweise Prüfung nicht sieht, und wann lohnt es sich, wenn man auch seine Kosten je Aufruf mitzählt?** Aufwand wird in Knoten, Fehlschlägen, Propagationsaufrufen und Grundoperationen gezählt, nie in Sekunden.

## Modell

- **Gruppe.** Variablen mit endlichen Domänen (Mengen ganzer Zahlen), in einer Gruppe müssen alle Werte verschieden sein. Der Rotationsplan hat je eine Gruppe pro Zeile und pro Spalte.
- **Drei Stärken** der Propagation je Gruppe: **A** paarweise (festgelegter Wert fällt aus den anderen Domänen, kaskadierend), **B** A plus Bounds über Hall-Intervalle (nur Minimum und Maximum wandern; eigene Fassung), **C** Bereichskonsistenz nach Régin (maximales Matching, starke Zusammenhangskomponenten, Wechselwege von freien Werten). C ersetzt in der Umsetzung A und B, weil sie beide enthält; die Domänen nach der Wurzel erfüllen C ⊆ B ⊆ A.
- **Suche.** Variable mit der kleinsten Domäne (mehr als ein Wert, Gleichstand: kleinster Index), Werte aufsteigend, Propagation nach jeder Wahl. Ein **Knoten** ist jeder Zustand nach Propagation (Wurzel, jeder Zweig, jeder Lösungsknoten); ein **Fehlschlag** ein Knoten mit Widerspruch; ein Knotenbudget bricht die Suche ab (Ergebnis „mindestens“).
- **Grundoperation.** Ein Zugriff auf die Domäne einer Variablen (Länge, Minimum, Maximum, Mitgliedschaft, Streichen) oder ein besuchter Kantenzug im Variablen-Werte-Graphen (Matching-Suche, Graphaufbau, Tarjan, Erreichbarkeit, Prüfung). Gesamtkosten sind die Summe über alle Propagationsaufrufe der Suche.
- **Rotationsplan mit Lücken.** Ein durchmischtes lateinisches Quadrat (Zyklentausch ab dem zyklischen Quadrat, 30 n² Tausche, SplitMix64), daraus bleiben (100 − Lücken) Prozent der Zellen zufällig vorbelegt, ganzzahlig gerundet. Die Aufgabe ist **nach Konstruktion erfüllbar**.
- Mathematik, Symboltabelle und Quellen: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| Propagatoren A, B, C, Zähler, Erklärsätze der Schritte | `ald_algorithm.py` | Matching per Erweiterungspfade (nicht Hopcroft–Karp), Tarjan, Hall-Menge je Régin-Streichung |
| Propagationsschleife, Suche, Knotenbudget | `ald_search.py` | Warteschlange der Gruppen FIFO, Zähler in `Lauf` |
| Instanzen, Erzeuger, Lösungsprüfer | `ald_scenario.py` | H1 bis H3, Hall-Instanz, lateinisches Quadrat, Vorbelegung |
| SplitMix64 | `ald_rng.py` | Klasse **wörtlich** aus `reduktionskette-demo/red_scenario.py` (`SplitMix64`), dazu `mische` und `ziehe_zwei` |
| Kennzahlen, Verdikte, Sweep-Auswertung | `ald_evaluation.py` | alle Verdikte als reine Funktionen |
| Messskript des Sweeps | `tools/messung_sweep.py` | schreibt `ald_sweep_vorgerechnet.json` (**vorgerechnet, nicht live**) |

Vier Reiter in der App: **Eine Gruppe von Hand** (Schritt für Schritt, Matching-Graph, Handbeispiele H1 bis H3 und eigene Domänen), **Hall-Verletzung wächst** (live gerechnet, Vergleichsspalte aus der Vormessung der Planung), **Rotationsplan mit Lücken** (Einzelinstanz live, Sweep über 20 feste Zufalls-Seeds vorgerechnet), **Kosten je Aufruf**. Der Sweep ist unabhängig vom Zufalls-Seed und vom Knotenbudget der Seitenleiste.

## Befunde und Korrekturen gegenüber dem Plan

- **Zahlen der Vormessung, die sich nicht reproduzieren (überholt).** Die Vormessung nutzte Pythons `random`; die Rotationspläne dieser Demo entstehen aus dem SplitMix64 und sind andere Instanzen. Ordnung 10, 58 % Lücken: Median 21 / 15,5 / 14 Knoten (A / B / C) statt 18,5 / 15 / 13,5. Die Zahlen der **Hall-Instanzen und der Handbeispiele reproduzieren exakt** (41, 206, 1 237, 8 660; 1 120, 5 575, 33 412; 175 mit 96 Fehlschlägen).
- **„Im Median kaum Unterschied“ gilt je nach Lücken-Anteil unterschiedlich weit.** Median A durch Median C bei 58 % Lücken: 1,5 (Ordnung 10), 1,4 (12), 1,7 (14), **73,9 (15)**; bei 50 % Lücken 1,8 / 2,3 / **52,5** / **44,5**. Bei Ordnung 10 liegt das Verhältnis in allen vier Zellen unter 2 (1,4 bis 1,8); bei 50 und 55 % Lücken überschreitet es 2 schon bei Ordnung 12 (2,3 / 2,1), bei 58 und 62 % erst bei Ordnung 15 (73,9 / 3,5), bei Ordnung 14 liegt es dort bei 1,7 / 1,5 (Test `test_claim_median_verhaeltnis_waechst_mit_der_ordnung`).
- **Régin hat nicht „praktisch keine Sackgassen“.** Fehlschlag-Median 0 in jeder Zelle, aber in 68 von 380 Läufen mindestens ein Fehlschlag, höchstens 6. Abbruch am Budget nie; Maximum 76 Knoten (Plan: 77).
- **Die Lage der schwersten Lücken-Region reproduziert sich nicht.** Median der Fehlschläge von A bei Ordnung 15: 0 / 1 / 11,5 / 432 / 147 / 1 895 / 86,5 bei 35 / 40 / 45 / 50 / 55 / 58 / 62 % Lücken: größter Wert bei 58 %, nicht bei 55 % wie in der Vormessung. Bei 20 Seeds und einem Erzeuger behauptet die Demo keine Lage.
- **Kosten je Aufruf gemessen (Messlücke der Vormessung geschlossen).** Das Gesamtverdikt „Régin braucht weniger“ stimmt nicht überall: Siehe Befunde.
- **Aufrufzahlen der Vormessung (167 gegen 260,5 bei Ordnung 10, 58 %)** gelten nicht mehr: andere Instanzen und andere Warteschlange; hier 158 gegen 204,5 (Median der Läufe).
- **Stufe C ohne vorgeschaltetes A.** Der Plan nennt C „A plus Bereichskonsistenz“; die Umsetzung lässt für C die paarweise Prüfung weg, weil das Matching sie enthält. Knoten und Fehlschläge sind gleich (die Fixpunkte stimmen überein), nur Aufrufe und Grundoperationen unterscheiden sich.
- **Zeitangabe je Zeile.** Statt „etwa n Sekunden“ vorab nennt die App nach dem Lauf die gemessene Rechenzeit (nur Anzeige, nie ein Befund); vorab steht nur, dass die Rechnung bis zum Budget laufen kann.
- **Domänen-Editor** als ein Textfeld („1 3; 1 3; 1 2 3; 2 3 4“), 2 bis 8 Variablen, Werte 1 bis 8 (Plan: 3 bis 8 Variablen).
- **Kein PDF-Export** (der Plan nennt keinen).

## Befunde (gemessen, keine Behauptungen)

Zählungen der Suche sind exakt (deterministisch, ganzzahlig). Der Sweep (20 feste Zufalls-Seeds 0 bis 19, nur erfüllbare Instanzen, Knotenbudget 20 000, Gegenprobe jeder Antwort mit OR-Tools CP-SAT und unabhängigem Lösungsprüfer, 0 Abweichungen) steht in `ald_sweep_vorgerechnet.json`; `tests/test_claims_sweep.py` rechnet die Zellen von Ordnung 10 und zwei Zellen von Ordnung 15 live nach, die übrigen Zellen werden gezählt.

| Frage | Befund | Test |
|---|---|---|
| **Hall-Verletzung, k + 1 Variablen auf k Werte, ohne freie Variablen** | Knoten von A bei k = 3 bis 7: 10 / 41 / 206 / 1 237 / 8 660; bei k = 8 und 9 Abbruch am Budget von 50 000. Faktor je zusätzlichem Wert 5,0 (41 → 206), 6,0, 7,0. B und C: immer 1 Knoten. | `test_claim_hall_ohne_freie_variablen` |
| **Mit drei freien Variablen (je drei Werte)** | A bei k = 3 bis 6: 283 / 1 120 / 5 575 / 33 412; ab k = 7 Abbruch. 1 120 gegen 41 ist das 27,3-Fache (27 = 3³ Belegungen der freien Variablen); B und C: 1 Knoten. | `test_claim_hall_mit_freien_variablen_vervielfacht_den_schaden` |
| **H1** (a1 bis a4 auf drei Werte, vier freie Variablen mit zwei Werten) | A 175 Knoten mit 96 Fehlschlägen (15 + 16 · 10 von Hand), B und C 1 Knoten. | `test_claim_h1_h2_h3`, `test_h1_knoten_von_hand` |
| **H2** (x1 {1, 3}, x2 {1, 3}, x3 {1, 2, 3}, x4 {2, 3, 4}) | An der Wurzel: A legt 0 Variablen fest, B 1 (x4 = 4; 2 Werte gestrichen), C 2 (x3 = 2 und x4 = 4; 4 Werte gestrichen). | `test_claim_h1_h2_h3`, `test_h2_wurzel_pro_stufe` |
| **H3** (Rotationsplan 4 × 4, vier Vorbelegungen) | Nach der Wurzel festgelegte Zellen: A 4, B 6, C 8; Suche bis zur ersten Lösung in allen Stufen 3 Knoten ohne Fehlschlag, 4 Lösungen. | `test_claim_h1_h2_h3`, `test_h3_*` |
| **Rotationsplan, 58 % Lücken, Median / 90-Prozent-Rang / Maximum der Knoten (A, B, C), Abbrüche von 20** | Ordnung 10: 21 / 15,5 / 14, 69 / 26 / 17, 519 / 187 / 19, Abbrüche 0 / 0 / 0. Ordnung 12: 38,5 / 31,5 / 27,5, 5 727 / 223 / 34, 20 000 / 20 000 / 36, Abbrüche 1 / 1 / 0. Ordnung 14: 70,5 / 50 / 42, Maximum 20 000 / 20 000 / 47, Abbrüche 3 / 3 / 0. Ordnung 15: 3 844,5 / 63,5 / 52, Maximum 20 000 / 20 000 / 59, Abbrüche 7 / 5 / 0. | `test_claim_tabelle_58_prozent_alle_ordnungen` |
| **Abbrüche am Budget je Zelle** (Lücken 50 / 55 / 58 / 62 %) | A, Ordnung 10: 0 / 0 / 0 / 1; 12: 0 / 0 / 1 / 4; 14: 4 / 8 / 3 / 2; 15: 4 / 3 / 7 / 5; insgesamt **42 von 380 Läufen**. B (320 Läufe): 16. **C: nie, in allen 380 Läufen höchstens 76 Knoten.** In den 42 Läufen, in denen A abbricht, löst Régin mit 13 bis 74 Knoten. | `test_claim_abbrueche_von_a_und_b_je_zelle`, `test_claim_regin_bricht_nie_ab_und_braucht_hoechstens_76_knoten` |
| **Median-Verhältnis A zu C** | 58 % Lücken: 1,5 (Ordnung 10), 1,4 (12), 1,7 (14), 73,9 (15); 50 % Lücken: 1,8 / 2,3 / 52,5 / 44,5. Bei Ordnung 10 liegt das Verhältnis in allen vier Zellen unter 2; bei 50 und 55 % Lücken überschreitet es 2 schon bei Ordnung 12 (2,3 / 2,1), bei 58 und 62 % erst bei Ordnung 15 (73,9 / 3,5; bei Ordnung 14 dort 1,7 / 1,5). | `test_claim_median_verhaeltnis_waechst_mit_der_ordnung` |
| **Knoten je Lauf, C gegen A** | Über 380 Läufe braucht C in 335 weniger, in 37 gleich viele, in 8 mehr Knoten als A. | `test_claim_c_gegen_a_knoten_je_lauf` |
| **Fehlschläge von C** | Median 0 in jeder der 19 Zellen; in 68 von 380 Läufen mindestens einer, höchstens 6. | `test_claim_fehlschlaege_von_c` |
| **Festgelegte Zellen nach der Wurzel** | Ordnung 10, 58 % (42 Zellen vorbelegt): Median 44,5 (A), 44,5 (B), 46,5 (C). C legt in 281 von 380 Läufen mehr Zellen fest als A, B in 140 von 320; nie weniger (Teilmengenordnung je Lauf). | `test_claim_festgelegte_zellen_nach_der_wurzel`, `test_claim_teilmengenordnung_der_wurzel_je_lauf` |
| **Kosten je Aufruf** (Grundoperationen, Median je Zelle) | A 82 bis 238, B 467 bis 1 798, C 115 bis 259; C das 0,87- bis 1,63-Fache von A, B das 5,7- bis 8,9-Fache von A. Hall-Instanz k = 7: A 8 660 Aufrufe mit 72 Grundoperationen je Aufruf, C ein Aufruf mit 148. | `test_claim_kosten_je_aufruf_und_gesamt`, `test_claim_hall_kosten_je_aufruf_und_gesamt` |
| **Gesamtkosten** (Median der Summe der Grundoperationen) | A durch C: 0,87 (Ordnung 10), 0,80 (12), 1,12 (14), 39,1 (15) bei 58 % Lücken. In **5 von 19 Zellen kostet Régin im Median mehr Grundoperationen als die paarweise Suche** (Ordnung 10 mit 55, 58, 62 %, Ordnung 12 mit 58 %, Ordnung 14 mit 62 %); B ist teurer als C in jeder Zelle. Auf der Hall-Instanz k = 7: A 623 520, B 40, C 148. | `test_claim_kosten_je_aufruf_und_gesamt`, `test_claim_hall_kosten_je_aufruf_und_gesamt` |
| **Vormessung der Hall-Instanz** | Alle Knotenzahlen der Vergleichsspalte der App (`out_cp_v10_hall.txt` der Planung) werden reproduziert. | `test_claim_vormessung_der_planung_wird_reproduziert` |

Alle Aussagen gelten für diese Umsetzung (Matching bei jedem Aufruf neu, einfache kubische Bounds-Prüfung), diesen Erzeuger und die gemessenen Zellen.

## Ehrliche Grenzen

- **Nur erfüllbare Rotationspläne.** Die Unerfüllbarkeit ist nur an der Hall-Instanz gemessen; wie sich die Stärken auf unerfüllbaren Rotationsplänen verhalten, zeigt die Demo nicht.
- **Variablenwahl und Werteordnung sind fest.** Eine andere Wahl (etwa nach Fehlschlägen gewichtet) wurde nicht gemessen und könnte die paarweise Suche verbessern; die 42 Abbrüche von A gelten für die feste Wahl.
- **Ein Erzeuger, 20 Zufalls-Seeds je Zelle.** Die Aussagen über Median, 90-Prozent-Rang und Abbrüche schwanken bei so wenigen Instanzen; eine Zelle mit 20 Läufen sagt über den Schwanz wenig genauer als „kommt vor“. Die Lage einer schwersten Lücken-Region ist nicht gesichert und wird nicht behauptet.
- **Gomes und Selman (AAAI 1997)** fanden den schwersten Bereich bei etwa 42 % Vorbelegung für **zufällig vorbelegte** Quadrate; die Rotationspläne dieser Demo entstehen aus einem vollständigen Quadrat (andere Familie). Die Demo übernimmt die 42 % nicht.
- **Kosten sind Eigenschaften dieser Fassung.** Régin nach der Quelle nutzt Hopcroft–Karp und setzt das Matching fort; hier wird das Matching bei jedem Aufruf mit einfachen Erweiterungspfaden neu berechnet. Die Bounds-Stufe prüft alle Intervalle durch (kubisch in der Gruppengröße) und ist eine **eigene Fassung**; eine Quelle für Bounds-Konsistenz wurde nicht gelesen. Die Kostenverhältnisse sagen nichts über andere Umsetzungen.
- **Grundoperationen sind eine eigene Zähleinheit**, keine Zeit; ein Domänenzugriff und ein Kantenbesuch zählen gleich.
- **Der Sweep ist vorgerechnet, nicht live.** Die Einzelinstanz im Reiter 3 und die Tabelle im Reiter 2 werden live gerechnet; die Rechenzeit wird nach dem Lauf angezeigt, ist aber nie ein Befund.
- **Das Plotly-Diagramm im Reiter 2 zeichnet B und C auf dieselbe Linie** (beide 1 Knoten); die Tabelle darüber zeigt beide.

## Verifikation

- **Handbeispiele von Hand gerechnet:** H1 (175 Knoten, 96 Fehlschläge), H2 (Wurzel je Stärke, Matching, Komponenten, gestrichene Kanten), H3 (4 / 6 / 8 festgelegte Zellen, 3 Knoten, 4 Lösungen), Einheiten (Kaskade, Hall-Intervall, Matching, Hall-Menge) in `tests/test_algorithm.py`.
- **Orakel** (`tests/test_oracle_alldifferent.py`, anderer Rechenweg): Régin gegen die **Aufzählung aller Belegungen** (300 Zufallsdomänen mit 3 bis 6 Variablen, auch negative Werte); Bounds gegen **ihre Definition per Aufzählung** (Relaxierung auf die Intervalle) samt Korrektheit; maximales Matching gegen `scipy.sparse.csgraph.maximum_bipartite_matching`; Lösungszahl der Rotationspläne der Ordnung 4 gegen die Aufzählung aller 576 lateinischen Quadrate (40 Vorbelegungen); Erfüllbarkeit von Ordnung 8, 10, 12 (auch unerfüllbare Varianten) gegen **OR-Tools CP-SAT** (nur Test-venv); Hall-Menge jeder Régin-Streichung gegen die Definition. Ein größerer Scratch-Lauf (2 000 Zufallsgruppen mit 3 bis 6 Variablen, 458 davon mit Streichungen durch Régin) ergab 0 Abweichungen für Régin und für Bounds; er ist nicht Teil des Repos.
- **Eigenschaften** (`tests/test_properties.py`): keine Stärke schneidet eine Lösung ab; Propagation idempotent und monoton; C ⊆ B ⊆ A; Umbenennen der Werte ändert die Antwort nie; Hall-Verletzung scheitert in B und C an der Wurzel und A wächst mit k; Zweig-Test: jede Stärke streicht auf mindestens einer Instanz mehr als ihre Nachbarin.
- **Randfälle** (`tests/test_edge_cases.py`): leere Domäne, einelementige Domänen, doppelt vorbelegter Wert, Gruppe mit einer Variablen, negative Werte mit Lücken, mehr Werte als Variablen, Ordnung 1 und 2.
- **Claims:** jede Zahl der Tabelle oben in `tests/test_claims.py` und `tests/test_claims_sweep.py`. **Zahl-zu-Test:** siehe die Spalte „Test“; die Messungen der Planung (Vormessung der Hall-Instanzen) werden von `test_claim_vormessung_der_planung_wird_reproduziert` gegen die Konstanten der App gehalten.
- **Verdikte** (`tests/test_verdicts.py`): jede Schwelle und jede genannte Zahl an handgesetzten Werten; Layout, Presets und Oberfläche (`test_layout.py`, `test_presets.py`, `test_app.py`, `test_app_inhalt.py`), Footer, Laufzeit-Importe.
- **Zufall:** SplitMix64 mit den Referenzwerten der Konvention und, wenn `reduktionskette-demo` daneben liegt, Gleichheit mit dem Original (`tests/test_rng_scenario.py`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `ald_algorithm.py` | Propagatoren A, B, C, Zähler, Erklärsätze |
| `ald_search.py` | Propagationsschleife, Suche, Knotenbudget |
| `ald_scenario.py` | Instanzen, Erzeuger, Lösungsprüfer |
| `ald_rng.py` | SplitMix64 (Kopie aus `reduktionskette-demo`) |
| `ald_constants.py` | Regler-Grenzen, Farben, Presets, Vormessung der Hall-Instanz |
| `ald_evaluation.py` | Kennzahlen, Verdikte, Auswertung des Sweeps |
| `ald_layout.py` | Fester Kopf (Stylesheet) |
| `ald_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Knopf |
| `ald_visualization.py` | Plotly-Abbildungen (Matrix, Gitter, Matching-Graph, Verläufe; Achsen gesperrt) |
| `ald_sweep_vorgerechnet.json` | vorgerechneter Sweep (Messung dieses Repos) |
| `tools/messung_sweep.py` | Messskript des Sweeps (`--gegenprobe` braucht OR-Tools) |
| `app.py` | Streamlit-App |
| `requirements.txt` | Laufzeit-Bibliotheken: streamlit, pandas, plotly (ungepinnt) |
| `requirements-dev.txt` | Laufzeit plus pytest, scipy und OR-Tools (nur Gegenproben in den Tests und im Messskript) |
| `tests/` | Handbeispiele, Orakel, Eigenschaften, Randfälle, Claims, Verdikte, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Lernen aus Fehlschlägen** (Propagator erklärt seinen Schluss als Klausel): die paarweise Suche zählt die freien Variablen mit, das behebt hier nur das Mengenargument, nicht das Lernen; Lernen gehört in ein anderes Stück der Linie.
- **Gewichtung der Variablenwahl nach Fehlschlägen**, inkrementelles Matching, Hopcroft–Karp und schnellere Bounds-Algorithmen: wären eigene Messungen.
- **Unerfüllbare Rotationspläne** als Messreihe.
- **PDF-Export** und Vergleich mit Industrie-Lösern; OR-Tools steht nur in den Tests und im Messskript.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Der Sweep lässt sich neu erzeugen (mehrere Minuten): `python tools/messung_sweep.py --gegenprobe`.

Gebaut mit Streamlit, Plotly und Pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
