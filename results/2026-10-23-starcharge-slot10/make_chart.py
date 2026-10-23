"""Render the Starcharge slot 10 charts from data.json.

timeline: every CSMS command (request -> station response) and every
station-initiated message over the session. latency: response time per
CSMS command. Times AEDT.

Run from this folder:

    python3 make_chart.py
"""
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
GOOD, CRITICAL, BLUE = "#0ca30c", "#d03b3b", "#2a78d6"
RESULT = {"Accepted": (GOOD, "o"), "Rejected": (CRITICAL, "X"), "CALLERROR": (CRITICAL, "X")}


def t(s):
    return datetime.strptime("2026-10-23 " + s.split(".")[0], "%Y-%m-%d %H:%M:%S").replace(
        microsecond=int((s.split(".") + ["0"])[1].ljust(6, "0")[:6]))


def frame(ax):
    ax.set_facecolor(SURFACE)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)


d = json.loads((HERE / "data.json").read_text())

# Timeline: one row per command family, station messages and heartbeats below.
families = []
for name, *_ in d["commands"]:
    fam = name.split(" (")[0].split(" 96")[0]
    if fam not in families:
        families.append(fam)
rows = families + ["Station-initiated", "NotifyReport", "Heartbeat"]
y = {r: len(rows) - 1 - i for i, r in enumerate(rows)}

fig, ax = plt.subplots(figsize=(11, 5.2), dpi=150)
fig.patch.set_facecolor(SURFACE)
frame(ax)
for r in rows:
    ax.axhline(y[r], color=GRID, linewidth=0.8, zorder=1)
for name, sent, ack, result in d["commands"]:
    fam = name.split(" (")[0].split(" 96")[0]
    colour, marker = RESULT[result]
    ax.scatter(t(sent), y[fam], marker=">", s=45, color=BLUE, zorder=3)
    ax.scatter(t(ack), y[fam], marker=marker, s=60, color=colour, edgecolors=SURFACE, linewidths=1.2, zorder=4)
for name, ts in d["station"]:
    ax.scatter(t(ts), y["Station-initiated"], marker="D", s=28, color=MUTED, zorder=3)
s0, s1, n = d["notify_report"]
ax.plot([t(s0), t(s1)], [y["NotifyReport"]] * 2, color=MUTED, linewidth=5, solid_capstyle="butt", zorder=2)
ax.text(t(s1), y["NotifyReport"] + 0.25, f"  {n} messages", fontsize=7.5, color=INK2, va="bottom")
for ts in d["heartbeats"]:
    ax.scatter(t(ts), y["Heartbeat"], marker="|", s=80, color=MUTED, zorder=3)
for label, ts in d["events"]:
    ax.axvline(t(ts), color=CRITICAL if "crash" in label else MUTED, linewidth=0.9, linestyle="--", zorder=1)
    crash = "crash" in label
    ax.text(t(ts), len(rows) - 0.4, (label + " ") if crash else (" " + label), fontsize=7.5, color=INK2,
            va="bottom", ha="right" if crash else "left")
for label, ts in d["station"][:2]:
    ax.axvline(t(ts), color=MUTED, linewidth=0.6, linestyle=":", zorder=1)
ax.text(t("16:28:37"), -0.9, " empty-ID connect", fontsize=7.5, color=MUTED)
ax.text(t("16:30:19"), -0.9, "                              STARCHARGE-01", fontsize=7.5, color=MUTED)
ax.set_yticks([y[r] for r in rows], rows, color=INK)
ax.set_ylim(-1.2, len(rows) - 0.1)
ax.set_xlim(t("16:28:00"), t("16:49:00"))
ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 2)))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.grid(axis="x", color=GRID, linewidth=0.6)
ax.set_title("Starcharge STARCHARGE-01 (OCPP 2.1) and the lab CSMS, 23 Oct 2026 (AEDT): commands sent and acknowledged",
             color=INK, loc="left", fontsize=10.5)
handles = [Line2D([], [], linestyle="", marker=">", color=BLUE, markersize=7, label="CSMS request sent"),
           Line2D([], [], linestyle="", marker="o", color=GOOD, markersize=7, label="Station response: Accepted"),
           Line2D([], [], linestyle="", marker="X", color=CRITICAL, markersize=7, label="Rejected / CALLERROR"),
           Line2D([], [], linestyle="", marker="D", color=MUTED, markersize=6, label="Station-initiated message")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=4, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"starcharge-timeline.{ext}", facecolor=SURFACE)

# Latency: request -> response per command.
cmds = d["commands"]
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
fig.patch.set_facecolor(SURFACE)
frame(ax)
ax.grid(axis="x", color=GRID, linewidth=0.8)
for i, (name, sent, ack, result) in enumerate(reversed(cmds)):
    ms = (t(ack) - t(sent)).total_seconds() * 1000
    colour = RESULT[result][0]
    ax.barh(i, ms, height=0.55, color=colour)
    ax.text(ms + 8, i, f"{ms:.0f} ms  {result}", va="center", fontsize=7.5, color=INK2)
ax.set_yticks(range(len(cmds)), [f"{c[1][:8]}  {c[0]}" for c in reversed(cmds)], color=INK, fontsize=7.5)
ax.set_xlim(0, 1400)
ax.set_xlabel("Request to response (ms), as logged by CitrineOS", color=INK2, fontsize=8)
ax.set_title("Starcharge answered every CSMS command, all within 1.1 s (median 0.18 s)",
             color=INK, loc="left", fontsize=10.5)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"starcharge-latency.{ext}", facecolor=SURFACE)
