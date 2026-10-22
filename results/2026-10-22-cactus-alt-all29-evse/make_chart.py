"""Render the Cactus ALT-ALL-29 run 76307 chart (EVSE's Ocular charger) from data.json and lab_data.json.

Cactus side (data.json): the import limit Cactus set and the 60 s site and DER readings ODE posted.
Lab side (lab_data.json): the TxProfile limits the bridge sent to the charger, the charger's power
from its energy register, and its charging state. Times AEDT.

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
BLUE, ORANGE, GREEN, VIOLET = "#2a78d6", "#eb6834", "#2e7d32", "#7b4fc9"


def at(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(AEDT).replace(tzinfo=None)


def local(ts):
    return datetime.fromtimestamp(ts, AEDT).replace(tzinfo=None)


d = json.loads((HERE / "data.json").read_text())
lab = json.loads((HERE / "lab_data.json").read_text())
start, end = at(d["timestampStart"]), at(d["timestampStatus"])

imp = [(at(t), w / 1000) for t, w in lab["odeImportLimitW"]] + [(end, 0)]

# The limit the charger held: the latest TxProfile at each second, read at its offset.
sends = [(at(p["sent"]), at(p["startSchedule"]), p["periods"]) for p in lab["txProfiles"]]
px, py = [], []
t = sends[0][0]
while t <= end:
    sent = [s for s in sends if s[0] <= t]
    if sent:
        _, st, periods = sent[-1]
        off = (t - st).total_seconds()
        lim = [w for sp, w in periods if off >= sp]
        px.append(t)
        py.append(lim[-1] / 1000 if lim else None)
    t += timedelta(seconds=1)

# Charger power from its energy register over about 60 s (4 readings 15 s apart).
meter = [(at(t), wh) for t, wh in lab["meterWh"]]
cx, cy = [], []
for a, b in zip(meter, meter[4:]):
    dt = (b[0] - a[0]).total_seconds()
    cx.append(b[0] - timedelta(seconds=dt / 2))
    cy.append((b[1] - a[1]) * 3.6 / dt)


def series(name):
    xs, ys = [], []
    # ODE stamps each 60 s average with the start of its window here.
    for r in sorted((r for r in d["readings"] if r["desc"] == name), key=lambda r: r["start"]):
        x = local(r["start"])
        xs += [x, x + timedelta(seconds=60)]
        ys += [r["value"] / 1000] * 2
    return xs, ys


fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(GRID)

states = [(at(t), s) for t, s in lab["chargingState"]]
for i, (t, s) in enumerate(states):
    if s == "SuspendedEVSE":
        ax.axvspan(t, states[i + 1][0] if i + 1 < len(states) else end, color=GRID, alpha=0.7, linewidth=0)

ax.step([x for x, _ in imp], [y for _, y in imp], where="post", color=BLUE, linewidth=2,
        label="Cactus import limit (ODE): 200 % ramp, then 50 / 40 / 30 / 0 % of 10 kW")
ax.plot(px, py, color=ORANGE, linewidth=2, label="TxProfile limit sent to the charger (site headroom)")
ax.plot(*series("Site Avg Real Power (W) - Net"), color=VIOLET, linewidth=1.6,
        label="Site net, 60 s average (+ import)")
ax.plot(cx, cy, color=GREEN, linewidth=1.6, marker="o", markersize=3,
        label="Charger power, from its energy register")
for t, _, _ in sends:
    ax.plot([t], [-0.7], marker="|", color=INK2, markersize=7)
ax.text(sends[0][0], -1.5, "TxProfile sends, all Accepted", fontsize=8, color=INK2)
ax.text(1, 1.01, "grey: charger SuspendedEVSE", transform=ax.transAxes, ha="right", fontsize=8, color=MUTED)
ax.set_ylim(-2, 21)
ax.set_xlim(start - timedelta(seconds=30), end + timedelta(seconds=30))
ax.set_ylabel("kW", color=INK2)
ax.xaxis.set_major_locator(mdates.MinuteLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.tick_params(colors=INK2)
ax.set_title("Cactus ALT-ALL-29 run 76307 with EVSE's Ocular charger (22 Oct 2026, AEDT): all criteria passed",
             color=INK, loc="left", fontsize=11)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"alt-all29-evse-chart.{ext}", facecolor=SURFACE)
