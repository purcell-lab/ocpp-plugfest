"""Render the Cactus ALT-ALL-29 run 76002 chart from data.json.

The import limit Cactus set (DERC1-5, each 2 minutes) and the 60 s readings ODE
posted: site net and DER net (Cactus sign: + export / generation, - import /
consumption for the DER). Times AEDT.

Run from this folder:

    python3 make_chart.py
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
AEDT = timezone(timedelta(hours=11))
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, GREEN = "#2a78d6", "#eb6834", "#2e7d32"


def offset(s):
    if s == "start":
        return 0
    m, _, rest = s.partition("m")
    if not rest and m.endswith("s"):
        return int(m[:-1])
    return int(m) * 60 + (int(rest.rstrip("s")) if rest else 0)


def local(ts):
    return datetime.fromtimestamp(ts, AEDT).replace(tzinfo=None)


d = json.loads((HERE / "data.json").read_text())
end = datetime.fromisoformat(d["timestampStatus"].replace("Z", "+00:00")).astimezone(AEDT).replace(tzinfo=None)
origin = end - timedelta(minutes=10)
imp = [(origin + timedelta(seconds=offset(p["offset"])), p["watts"])
       for s in d["dataStreams"] if s["label"] == "/derp/1 opModImpLimW" for p in s["data"]]
imp = [(x, w) for x, w in imp if x <= end]


def series(name):
    pts = [(local(r["start"]), r["value"] / 1000) for r in d["readings"] if r["desc"] == name]
    xs, ys = [], []
    # ODE stamps each 60 s average with the end of its window.
    for x, y in pts:
        xs += [x - timedelta(seconds=60), x]
        ys += [y, y]
    return xs, ys


fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(GRID)
ax.step([x for x, _ in imp], [w / 1000 if w is not None else None for _, w in imp], where="post", color=BLUE,
        linewidth=2, label="Import limit (DERC1 200 %, then 50 / 40 / 30 / 0 %)")
ax.plot(*series("Site Avg Real Power (W) - Net"), color=GREEN, linewidth=1.6, label="Site net, 60 s average (+ import)")
ax.plot(*[(xs, [-y for y in ys]) for xs, ys in [series("DER Average Real Power (W) - Net")]][0], color=ORANGE,
        linewidth=1.6, label="V2G EV, 60 s average (+ charging, - discharging)")
ax.axhline(25, color=MUTED, linewidth=0.8, linestyle="--")
ax.text(origin + timedelta(seconds=20), 25.6, "EV rating 25 kW", fontsize=8, color=MUTED)
ax.set_ylim(-3, 72)
ax.set_ylabel("kW", color=INK2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.tick_params(colors=INK2)
ax.set_title("Cactus ALT-ALL-29 run 76002 (21 Oct 2026, AEDT): all criteria passed, 9 site and 9 DER readings",
             color=INK, loc="left", fontsize=11)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"alt-all29-chart.{ext}", facecolor=SURFACE)
