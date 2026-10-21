"""Render the Cactus LOA-10 run 75995 chart from data.json.

The import limit each program set (DERP1, the higher priority; DERP6, the
lower; the default), the limit that applies by primacy, and the V2G EV's
power as ODE reported it to Cactus (DER readings, 20 s points). Times AEDT.

Run from this folder:

    python3 make_chart.py
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
AEDT = timedelta(hours=11)
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#2e7d32", "#b8b6b0"


def offset(s):
    if s == "start":
        return 0
    m, _, rest = s.partition("m")
    if not rest and "s" in m:
        return int(m.rstrip("s"))
    return int(m) * 60 + (int(rest.rstrip("s")) if rest else 0)


def parse(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).replace(tzinfo=None) + AEDT


d = json.loads((HERE / "data.json").read_text())
origin = parse(d["timestampStatus"]) - timedelta(seconds=offset(d["nowOffset"]))
streams = {s["label"]: [(origin + timedelta(seconds=offset(p["offset"])), p["watts"]) for p in s["data"]]
           for s in d["dataStreams"]}

xs = [x for x, _ in streams["Default opModImpLimW"]]
derp1 = dict(streams["/derp/1 opModImpLimW"])
derp6 = dict(streams["/derp/6 opModImpLimW"])
dflt = dict(streams["Default opModImpLimW"])
applied = [derp1[x] if derp1[x] is not None else derp6[x] if derp6[x] is not None else dflt[x] for x in xs]
ev = [(x, -w / 1000 if w is not None else None) for x, w in streams["Device Power"]]

steps = d["stepStatus"]
disc = (parse(steps["POST-DERC-4-RESPONSE-STARTED"]["completedAt"]),
        parse(steps["POST-DERC-4-RESPONSE-COMPLETED"]["completedAt"]))
# DERC4 (DERP1) sets opModConnect false and a 0 W load limit, so nothing is imported for load while it runs.
applied = [0 if disc[0] <= x < disc[1] else v for x, v in zip(xs, applied)]

fig, ax = plt.subplots(figsize=(12, 5.2), dpi=150)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(GRID)

ax.axvspan(*disc, color=GREY, alpha=0.25, linewidth=0)
ax.text(disc[0] + (disc[1] - disc[0]) / 2, 52, "DERC4\ndisconnect", ha="center", va="top", fontsize=8, color=INK2)
ax.step(xs, [v / 1000 if v is not None else None for v in applied], where="post", color=BLUE, linewidth=2,
        label="Import limit applied by primacy (DERP1 > DERP6 > default; 0 W while disconnected)")
ax.step(xs, [v / 1000 if v is not None else None for v in (derp6[x] for x in xs)], where="post", color=BLUE,
        linewidth=1, linestyle=":", label="DERP6 (lower priority) control")
ax.plot([x for x, _ in ev], [w for _, w in ev], color=ORANGE, linewidth=1.8,
        label="V2G EV, + charging / - discharging (DER reading to Cactus)")
ax.axhline(25, color=MUTED, linewidth=0.8, linestyle="--")
ax.text(xs[2], 25.6, "EV rating 25 kW", fontsize=8, color=MUTED)
ax.set_ylim(-3, 72)
ax.set_ylabel("kW", color=INK2)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.tick_params(colors=INK2)
ax.set_title("Cactus LOA-10 run 75995 (21 Oct 2026, AEDT): 46/46 steps, no warnings", color=INK, loc="left",
             fontsize=12)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"loa10-chart.{ext}", facecolor=SURFACE)
