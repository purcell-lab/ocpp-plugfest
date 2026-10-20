"""Render the Cactus ALL-23 chart from data.json.

Top: run 75381 (ODE 0.1.5) on an AEDT time axis. It shows the limit ODE held
through the comms outage (shaded), the V2G EV's discharge, and the ramps to the
0 W default and to the post-restore 200 % control.

Bottom: when ODE polled the program list (and with it the DERControlList),
measured from the moment Cactus cut comms, for run 75362 (ODE 0.1.4) and run
75381 (ODE 0.1.5). Comms come back at +12 min and the test then waits 2 min.

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
DAY = "2026-10-20 "
SURFACE, INK, INK2, MUTED, GRID, BAND = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#efeeea"
BLUE, ORANGE = "#2a78d6", "#eb6834"


def t(hms):
    return datetime.fromisoformat(DAY + hms)


def steps(points, until):
    xs, ys = [], []
    for i, (x, y) in enumerate(points):
        nxt = points[i + 1][0] if i + 1 < len(points) else until
        xs += [x, nxt]
        ys += [y, y]
    return xs, ys


def style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def secs(hms, ref):
    return (t(hms) - t(ref)).total_seconds() / 60


def main():
    d = json.loads((HERE / "data.json").read_text())
    r = d["runs"]["75381"]
    x0, x1 = t("12:04:30"), t("12:20:40")
    cut, back, end = t("12:06:19"), t("12:18:20"), t("12:20:20")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, (a, b) = plt.subplots(2, 1, figsize=(10.5, 8.2), facecolor=SURFACE,
                               gridspec_kw={"height_ratios": [1.5, 1], "hspace": 0.55})
    style(a)
    a.axvspan(cut, back, color=BAND, zorder=0)
    a.text(cut + (back - cut) / 2, 30.5, "Comms cut by Cactus (HTTP 500): ODE runs its cached schedule",
           ha="center", va="top", color=INK2, fontsize=8.5)
    top = 33
    lim = [(t(h), w / 1000) for h, w in r["ode_export_limit_w"] if w >= 0]
    lx, ly = steps(lim, x1)
    a.plot(lx, [min(y, top - 1) for y in ly], color=INK2, linewidth=1.5, label="ODE export limit (cached schedule, then post-restore control)")
    ev = [(t(h), -w / 1000) for h, w in r["ev_power_w"] if w is not None]
    ex, ey = steps(ev, x1)
    a.plot(ex, ey, color=ORANGE, linewidth=2, label="EV discharge (CitrineOS)")
    for h, label in [("12:04:57", "DERC1\n200 %"), ("12:06:57", "DERC2\n20 %"), ("12:08:57", "DERC3\n40 %"),
                     ("12:10:57", "DERC4\n30 %"), ("12:12:57", "DERC5\n40 %"), ("12:14:57", "default\n0 W")]:
        a.axvline(t(h), color=GRID, linewidth=0.8, zorder=0)
        a.text(t(h) + timedelta(seconds=6), 20, label, ha="left", va="top", color=MUTED, fontsize=7.5)
    a.annotate("70 kW", xy=(t("12:06:30"), top - 1), xytext=(t("12:06:30"), top - 4.5), ha="center", color=INK2,
               fontsize=8, arrowprops={"arrowstyle": "->", "color": INK2, "lw": 0.8})
    a.annotate("restore 12:18:20,\nDERControlList GET 12:18:37,\nramp to 200 % at 2.1 kW/s", xy=(t("12:18:45"), 18),
               xytext=(t("12:15:30"), 25), color=INK2, fontsize=8, arrowprops={"arrowstyle": "->", "color": INK2, "lw": 0.8})
    a.set_xlim(x0, x1)
    a.set_ylim(-1, top)
    a.set_ylabel("kW")
    a.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 2)))
    a.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    a.set_title("ALL-23 run 75381 (ODE 0.1.5): passed, 5/5 steps", loc="left", fontsize=11.5, pad=8)
    a.legend(loc="upper center", frameon=False, fontsize=8.5, ncol=2, bbox_to_anchor=(0.5, -0.1))

    style(b)
    b.grid(axis="x", color=GRID, linewidth=0.8)
    b.axvspan(0, 12, color=BAND, zorder=0)
    b.axvspan(12, 14, color="#e1ecf8", zorder=0)
    b.text(13, 1.75, "120 s to poll\nafter restore", ha="center", va="center", color=INK2, fontsize=8)
    rows = [("75362", "Run 75362\nODE 0.1.4", "10:07:47", 1), ("75381", "Run 75381\nODE 0.1.5", "12:06:19", 0)]
    for run, label, ref, y in rows:
        polls = d["runs"][run]["derp_polls"]
        for h, s in polls:
            x = secs(h, ref)
            if s == 200:
                b.plot(x, y, marker="o", color=BLUE, markersize=9, markeredgecolor=SURFACE, zorder=3)
            else:
                b.plot(x, y, marker="x", color=INK2, markersize=8, mew=2, zorder=3)
    b.plot(secs("10:23:55", "10:07:47"), 1, marker="o", markerfacecolor="none", markeredgecolor=MUTED, markersize=9)
    b.annotate("next poll due ~16.1 min:\nrun already finished", xy=(16.1, 1), xytext=(14.4, 1.45), color=INK2, fontsize=8,
               arrowprops={"arrowstyle": "->", "color": INK2, "lw": 0.8})
    b.annotate("GET 17 s after restore", xy=(12.3, 0), xytext=(14.4, 0.45), color=INK2, fontsize=8,
               arrowprops={"arrowstyle": "->", "color": INK2, "lw": 0.8})
    b.plot([], [], marker="o", color=BLUE, linestyle="none", label="poll answered (200)")
    b.plot([], [], marker="x", color=INK2, mew=2, linestyle="none", label="poll failed (500, after 5 retries)")
    b.set_yticks([1, 0])
    b.set_yticklabels([r[1] for r in rows])
    b.set_ylim(-0.6, 2.2)
    b.set_xlim(-1, 17)
    b.set_xticks(range(0, 17, 2))
    b.set_xlabel("Minutes since Cactus cut comms (restored at 12 min)")
    b.set_title("Program-list polls: 300 s after a failure (0.1.4) versus the server's 60 s (0.1.5)", loc="left", fontsize=11.5, pad=8)
    b.legend(loc="upper left", frameon=False, fontsize=8, ncol=2, bbox_to_anchor=(0.0, 1.0))
    fig.text(0.01, 0.005, "Times AEDT, 20 October 2026. Limit: lab helper fed from ODE's limits/csipAus. EV: CitrineOS meter values. "
             "Polls: Cactus request log, GET /edev/1/fsa/1/derp (retries within 20 s shown once).", color=MUTED, fontsize=7.5)
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"all23-chart.{ext}", dpi=150, facecolor=SURFACE, bbox_inches="tight")


if __name__ == "__main__":
    main()
