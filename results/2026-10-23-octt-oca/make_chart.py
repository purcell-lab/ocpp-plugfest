"""Render the OCTT (OCA) session charts from data.json.

timeline: every message outcome by type over the session, with the CitrineOS
App version in use. profiles: SetChargingProfile outcomes by profile shape.
Times AEDT.

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
GOOD, WARNING, CRITICAL = "#0ca30c", "#fab219", "#d03b3b"
BAND = ["#f1f0ec", "#e8eef8", "#e6f2e6"]
STYLE = {
    "accepted": dict(marker="o", color=GOOD, label="Accepted / connected"),
    "rejected": dict(marker="X", color=CRITICAL, label="Rejected / refused"),
    "problem": dict(marker="^", color=WARNING, label="Reply missing or wrong ongoingIndicator"),
}


def t(s):
    return datetime.strptime("2026-10-23 " + (s if s.count(":") == 2 else s + ":00"), "%Y-%m-%d %H:%M:%S")


def frame(ax):
    ax.set_facecolor(SURFACE)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)


d = json.loads((HERE / "data.json").read_text())

# Timeline
lanes = list(d["lanes"])
fig, ax = plt.subplots(figsize=(11, 4.6), dpi=150)
fig.patch.set_facecolor(SURFACE)
frame(ax)
for i, v in enumerate(d["versions"]):
    ax.axvspan(t(v["from"]), t(v["to"]), color=BAND[i], zorder=0, linewidth=0)
    ax.text(t(v["from"]), len(lanes) - 0.45, " " + v["label"], fontsize=8, color=INK2, va="bottom")
for m in d["markers"]:
    ax.axvline(t(m["time"]), color=MUTED, linewidth=0.8, linestyle="--", zorder=1)
    ax.text(t(m["time"]), -0.75, " " + m["label"], fontsize=7.5, color=MUTED, va="center")
for y, lane in enumerate(reversed(lanes)):
    ax.axhline(y, color=GRID, linewidth=0.8, zorder=1)
    for time, outcome, _ in d["lanes"][lane]:
        s = STYLE[outcome]
        ax.scatter(t(time), y, marker=s["marker"], s=70, color=s["color"], edgecolors=SURFACE, linewidths=1.5, zorder=3)
ax.set_yticks(range(len(lanes)), list(reversed(lanes)), color=INK)
ax.set_ylim(-1.1, len(lanes) - 0.1)
ax.set_xlim(t("11:20"), t("12:42"))
ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 10)))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.grid(axis="x", color=GRID, linewidth=0.6)
ax.set_title("OCTT (OCA) on OCPP 2.1 against the lab CSMS, 23 Oct 2026 (AEDT): every message outcome",
             color=INK, loc="left", fontsize=11)
handles = [Line2D([], [], linestyle="", marker=s["marker"], color=s["color"], markersize=8, label=s["label"])
           for s in STYLE.values()]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"octt-timeline.{ext}", facecolor=SURFACE)

# Profiles
rows = d["profiles"]
fig, ax = plt.subplots(figsize=(11, 3.2), dpi=150)
fig.patch.set_facecolor(SURFACE)
frame(ax)
ax.grid(axis="x", color=GRID, linewidth=0.8)
for y, r in enumerate(reversed(rows)):
    if r["accepted"]:
        ax.barh(y, r["accepted"], height=0.5, color=GOOD, edgecolor=SURFACE, linewidth=2)
    ax.barh(y, r["rejected"], left=r["accepted"], height=0.5, color=CRITICAL, edgecolor=SURFACE, linewidth=2)
    total = r["accepted"] + r["rejected"]
    ax.text(total + 0.08, y, f"{r['accepted']} of {total} accepted  ({r['ids']})", va="center", fontsize=8, color=INK2)
ax.set_yticks(range(len(rows)), [r["shape"] for r in reversed(rows)], color=INK)
ax.set_xlim(0, 8.5)
ax.set_xlabel("SetChargingProfile requests", color=INK2, fontsize=8)
ax.set_title("TxProfiles sent to OCTT by shape: only the A charging limits were ever accepted",
             color=INK, loc="left", fontsize=11)
handles = [plt.Rectangle((0, 0), 1, 1, color=GOOD, label="Accepted"),
           plt.Rectangle((0, 0), 1, 1, color=CRITICAL, label="Rejected (no statusInfo)")]
ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=8)
fig.tight_layout()
for ext in ("svg", "png"):
    fig.savefig(HERE / f"octt-profiles.{ext}", facecolor=SURFACE)
