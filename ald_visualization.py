"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import ald_algorithm as A
import ald_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.22), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_matrix(inst, vorher, nachher, hervorhebung=()):
    """Domänen-Matrix: Zeile je Variable, Spalte je Wert. Grau = Wert nie in der Domäne, hellgrün = in der Domäne, rot = in diesem Schritt gestrichen,
    dunkelgrün = Variable ist festgelegt. `vorher`/`nachher`: Domänen (Mengenlisten) vor und nach dem betrachteten Schritt."""
    werte = sorted({w for d in inst.doms for w in d})
    z, text = [], []
    for i in range(inst.n):
        zeile, tzeile = [], []
        for w in werte:
            if w not in inst.doms[i]:
                code, t = 0, ""
            elif w in nachher[i]:
                code, t = (3, "✓") if len(nachher[i]) == 1 else (1, "")
            elif w in vorher[i]:
                code, t = 2, "✗"
            else:
                code, t = 0, ""
            zeile.append(code)
            tzeile.append(t)
        z.append(zeile)
        text.append(tzeile)
    farben = [(0.0, C.COLOR_OUT), (0.25, C.COLOR_OUT), (0.25, C.COLOR_IN), (0.5, C.COLOR_IN), (0.5, C.COLOR_GONE), (0.75, C.COLOR_GONE), (0.75, C.COLOR_FIXED), (1.0, C.COLOR_FIXED)]
    fig = go.Figure(go.Heatmap(z=z, x=[str(w) for w in werte], y=list(inst.namen), text=text, texttemplate="%{text}", colorscale=farben, zmin=0, zmax=3,
                               showscale=False, xgap=2, ygap=2, hovertemplate="%{y}, Wert %{x}<extra></extra>"))
    fig.update_xaxes(title_text="Wert", type="category", side="top")
    fig.update_yaxes(autorange="reversed", type="category")
    return _base(fig, height=max(240, 46 * inst.n + 80))


def build_grid(ordnung, namen, doms, vorher=None):
    """Rotationsplan als Gitter: festgelegte Zellen mit ihrem Wert (grün), offene Zellen mit den verbleibenden Werten; in diesem Schritt gestrichene Werte stehen nicht mehr da."""
    fig = go.Figure()
    for r in range(ordnung):
        for c in range(ordnung):
            d = sorted(doms[r * ordnung + c])
            fest = len(d) == 1
            fig.add_shape(type="rect", x0=c, x1=c + 1, y0=r, y1=r + 1, line=dict(color="rgba(128,128,128,0.6)", width=1),
                          fillcolor=C.COLOR_FIXED if fest else "rgba(0,0,0,0)")
            fig.add_annotation(x=c + 0.5, y=r + 0.5, text=(f"<b>{d[0]}</b>" if fest else " ".join(str(w) for w in d)), showarrow=False,
                               font=dict(color="white" if fest else "gray", size=18 if fest else 11))
    fig.update_xaxes(range=[0, ordnung], tickvals=[c + 0.5 for c in range(ordnung)], ticktext=[f"Tag {c + 1}" for c in range(ordnung)], side="top", showgrid=False, zeroline=False)
    fig.update_yaxes(range=[ordnung, 0], tickvals=[r + 0.5 for r in range(ordnung)], ticktext=[f"M{r + 1}" for r in range(ordnung)], showgrid=False, zeroline=False)
    return _base(fig, height=90 * ordnung + 80)


def build_matching(inst, dom, gruppe=0):
    """Bipartiter Graph Variablen (links) und Werte (rechts) für eine Gruppe: Kopplungskanten fett, Kanten, die Régin streicht, rot gestrichelt,
    übrige Domänenkanten grau; die Knoten tragen die Farbe ihrer starken Zusammenhangskomponente. Gibt (Figur, Matching-Größe, Zahl der Variablen) zurück."""
    g = list(inst.gruppen[gruppe])
    a = A.regin_analyse(dom, g, A.Zaehler())
    werte = sorted({w for i in g for w in dom[i]})
    ypos = {i: len(g) - 1 - p for p, i in enumerate(g)}
    wpos = {w: (len(g) - 1) * (len(werte) - 1 - t) / max(1, len(werte) - 1) for t, w in enumerate(werte)}
    fig = go.Figure()

    def kante(i, w, farbe, breite, dash):
        fig.add_trace(go.Scatter(x=[0, 1], y=[ypos[i], wpos[w]], mode="lines", line=dict(color=farbe, width=breite, dash=dash), hoverinfo="skip", showlegend=False))

    streichen = set(a.get("streiche", []))
    for i in g:
        for w in sorted(dom[i]):
            if a["ok"] and a["mate_var"].get(i) == w:
                continue
            if (i, w) in streichen:
                kante(i, w, C.COLOR_GONE, 2, "dash")
            else:
                kante(i, w, "rgba(150,150,150,0.8)", 1, "solid")
    for i, w in a["mate_var"].items():
        kante(i, w, C.COLOR_FIXED, 5, "solid")
    palette = ["#4c78a8", "#f58518", "#54a24b", "#b279a2", "#e45756", "#72b7b2", "#eeca3b", "#9d755d"]
    if a["ok"]:
        komp = a["komp"]
        ids = sorted(set(komp.values()))
        dichte = {k: [n for n, kk in komp.items() if kk == k] for k in ids}
        farbe_von = {k: (palette[j % len(palette)] if len(dichte[k]) > 1 else "#bbbbbb") for j, k in enumerate(ids)}
        vfarben = [farbe_von[komp[("v", i)]] for i in g]
        wfarben = [farbe_von[komp[("w", w)]] for w in werte]
    else:
        vfarben = ["#bbbbbb" if i in a["mate_var"] else C.COLOR_GONE for i in g]
        wfarben = ["#bbbbbb"] * len(werte)
    fig.add_trace(go.Scatter(x=[0] * len(g), y=[ypos[i] for i in g], mode="markers+text", text=[inst.namen[i] for i in g], textposition="middle left",
                             marker=dict(size=22, color=vfarben, line=dict(color="white", width=1)), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[1] * len(werte), y=[wpos[w] for w in werte], mode="markers+text", text=[str(w) for w in werte], textposition="middle right",
                             marker=dict(size=22, color=wfarben, line=dict(color="white", width=1)), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(range=[-0.35, 1.25], visible=False)
    fig.update_yaxes(range=[-0.6, len(g) - 0.4], visible=False)
    return _base(fig, height=max(260, 55 * len(g) + 60)), a["groesse"], len(g)


def build_hall(zeilen):
    """Knoten je Stärke über k (logarithmische Achse); Läufe, die am Budget abbrachen, sind hohl gezeichnet (Untergrenze)."""
    fig = go.Figure()
    for st in C.STUFEN:
        xs = [z["k"] for z in zeilen]
        ys = [z[st].knoten for z in zeilen]
        offen = [z[st].abgebrochen for z in zeilen]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", name=C.STUFEN_KURZ[st], line=dict(color=C.STUFEN_FARBEN[st], width=3),
                                 marker=dict(size=10, color=[("white" if o else C.STUFEN_FARBEN[st]) for o in offen], line=dict(color=C.STUFEN_FARBEN[st], width=2)),
                                 hovertemplate="k = %{x}: %{y} Knoten<extra></extra>"))
    fig.update_xaxes(title_text="k (k + 1 Variablen auf k Werten)", dtick=1)
    fig.update_yaxes(title_text="Knoten bis zum Fehlschlag (logarithmisch)", type="log")
    return _base(fig)


def build_ecdf(zelle_stufen, budget):
    """Empirische Verteilungsfunktion der Knotenzahlen je Stärke über die festen Zufalls-Seeds; Abbrüche liegen am Budget (rechter Rand)."""
    fig = go.Figure()
    for st in C.STUFEN:
        if st not in zelle_stufen:
            continue
        knoten = sorted(z["knoten"] for z in zelle_stufen[st])
        n = len(knoten)
        fig.add_trace(go.Scatter(x=knoten, y=[(i + 1) / n for i in range(n)], mode="lines+markers", line=dict(shape="hv", color=C.STUFEN_FARBEN[st], width=3),
                                 name=C.STUFEN_KURZ[st], hovertemplate="%{x} Knoten: %{y:.0%} der Läufe<extra></extra>"))
    fig.add_vline(x=budget, line_dash="dot", line_color="gray", annotation_text="Budget", annotation_position="top left")
    fig.update_xaxes(title_text="Knoten (logarithmisch)", type="log")
    fig.update_yaxes(title_text="Anteil der Läufe", tickformat=".0%", range=[0, 1.02])
    return _base(fig)


def build_balken(werte: dict, titel: str, log=False):
    """Ein Balken je Stärke."""
    fig = go.Figure(go.Bar(x=[C.STUFEN_KURZ[s] for s in C.STUFEN if s in werte], y=[werte[s] for s in C.STUFEN if s in werte],
                           marker_color=[C.STUFEN_FARBEN[s] for s in C.STUFEN if s in werte], text=[f"{werte[s]:,.0f}".replace(",", " ") for s in C.STUFEN if s in werte],
                           textposition="outside", hoverinfo="skip"))
    fig.update_yaxes(title_text=titel, type="log" if log else "linear")
    return _base(fig, height=300)
