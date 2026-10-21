"""Render the Cactus ALL-21 run 76139 chart from data.json.

The 24 one-minute controls (export limit, as Cactus sets it), and the 60 s
readings ODE posted: site export and V2G discharge (both drawn positive).
Times AEDT.

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


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(AEDT).replace(tzinfo=None)


def local(ts):
    return datetime.fromtimestamp(ts, AEDT).replace(tzinfo=None)


d = json.loads((HERE / "data.json").read_text())
tl = d["timeline"]
origin, end = parse(tl["start"]), parse(d["timestampStatus"])
ex = next(s for s in tl["dataStreams"] if s["label"] == "/derp/1 opModExpLimW")["offsetWattValues"]
pts = [(origin + timedelta(seconds=i * tl["intervalSeconds"]), abs(w) / 1000) for i, w in enumerate(ex) if w is not None]


def series(name, sign=1):
    xs, ys = [], []
    # ODE stamps each 60 s average with the end of its window.
    for r in d["readings"]:
        if r["desc"] == name:
            x = local(r["start"])
            xs += [x - timedelta(seconds=60), x]
            ys += [sign * r["value"] / 1000] * 2
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
ax.step([x for x, _ in pts], [w for _, w in pts], where="post", color=BLUE, linewidth=2,
        label="Export limit (24 one-minute controls, 10-100 % of 35 kW)")
ax.plot(*series("Site Avg Real Power (W) - Net", -1), color=GREEN, linewidth=1.6, label="Site export, 60 s average")
ax.plot(*series("DER Average Real Power (W) - Net"), color=ORANGE, linewidth=1.6, label="V2G discharge, 60 s average")
on = parse(d["exportModeOn"])
ax.axvline(on, color=MUTED, linewidth=0.8, linestyle="--")
ax.text(on + timedelta(seconds=10), 34, "bridge export mode on", fontsize=8, color=MUTED)
ax.set_xlim(origin, end)
ax.set_ylim(-1, 37)
ax.set_ylabel("kW", color=INK2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.tick_params(colors=INK2)
ax.set_title("Cactus ALL-21 run 76139 (22 Oct 2026, AEDT): all 6 criteria passed; V2G discharge followed each control",
             color=INK, loc="left", fontsize=11)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"all21-chart.{ext}", facecolor=SURFACE)
