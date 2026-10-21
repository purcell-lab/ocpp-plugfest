"""Render the Cactus ALL-06 run 76007 chart from data.json.

The 60 s site and DER active-power readings ODE posted, and DERC1 (0 W import
and export, 5 minutes) over the 200 kW defaults. DER sign flipped to + charging.
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
start, end = parse(d["timestampStart"]), parse(d["timestampStatus"])
derc1 = parse(d["stepStatus"]["WAIT-CONTROL"]["startedAt"])


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
ax.step([start, derc1, end], [25, 0, 0], where="post", color=BLUE, linewidth=2,
        label="Import limit applied by the bridge (200 kW default capped at 25 kW; DERC1 0 W)")
ax.plot(*series("Site Avg Real Power (W) - Net"), color=GREEN, linewidth=1.6, label="Site net, 60 s average (+ import)")
ax.plot(*series("DER Average Real Power (W) - Net", -1), color=ORANGE, linewidth=1.6,
        label="V2G EV, 60 s average (+ charging)")
ax.axvspan(derc1, end, color=BLUE, alpha=0.06, linewidth=0)
ax.text(derc1 + timedelta(seconds=6), 27.2, "DERC1: 0 W import and export (EV kept charging)", fontsize=8, color=MUTED)
ax.set_xlim(start, end)
ax.set_ylim(-1, 29)
ax.set_ylabel("kW", color=INK2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.tick_params(colors=INK2)
ax.set_title("Cactus ALL-06 run 76007 (21 Oct 2026, AEDT): 8 / 8 criteria passed; the EV ignored the 0 W control",
             color=INK, loc="left", fontsize=11)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"all06-chart.{ext}", facecolor=SURFACE)
