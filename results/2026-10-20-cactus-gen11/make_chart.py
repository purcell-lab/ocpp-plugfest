"""Render the Cactus GEN-11 run 75354 chart from data.json.

Two panels on a shared AEDT time axis:
- the site: export as ODE posted it to Cactus, against the export limit in force
  (the active DERControl, else the default);
- the DER (solar plus the V2G EV, as ODE posted it) against the 35 kW setMaxW
  ODE reported.
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
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
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


def main():
    d = json.loads((HERE / "data.json").read_text())
    x0, x1 = t("08:58:00"), t("09:12:30")
    # ODE labels each 60 s average with the end of its window, so each value is
    # drawn over the minute before its timestamp.
    win = timedelta(seconds=60)
    site = [(t(h) - win, -w / 1000) for h, w in d["ode_site_net_w"]]
    der = [(t(h) - win, w / 1000) for h, w in d["ode_der_net_w"]]
    exp = []
    for r in d["cactus_limits_w"]:
        v = r["control_exp"] if r["control_exp"] is not None else r["default_exp"]
        if v is not None:
            exp.append((t(r["t"]), v / 1000))
    started = [(t(h), tag) for h, tag, kind in d["responses"] if kind == "Started"]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, (a, b) = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True, facecolor=SURFACE,
                               gridspec_kw={"height_ratios": [1.2, 1], "hspace": 0.3})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        for x, _ in started:
            ax.axvline(x, color=GRID, linewidth=0.8, zorder=0)
        ax.axvline(t("09:02:36"), color=MUTED, linewidth=1, linestyle=(0, (1, 2)), zorder=0)

    # Panel A: site export against the export limit (clipped at 40 kW so DERC1's 70 kW shows as an arrow).
    top = 40
    ex, ey = steps(exp, x1)
    a.plot(ex, [min(y, top - 1) for y in ey], color=INK2, linewidth=1.3, linestyle=(0, (3, 2)), label="Export limit in force")
    a.annotate("70 kW", xy=(t("09:00:13"), top - 1), xytext=(t("09:00:13"), top - 5), ha="center",
               color=INK2, fontsize=8.5, arrowprops={"arrowstyle": "->", "color": INK2, "lw": 0.8})
    sx, sy = steps(site, site[-1][0] + win)
    a.plot(sx, sy, color=BLUE, linewidth=2.2, label="Site export (ODE, 60 s averages)")
    for x, label in started:
        a.text(x, top - 0.3, label, rotation=90, ha="right", va="top", color=MUTED, fontsize=7.5)
    a.text(t("09:02:40"), 3, "bridge fix\n09:02:36", ha="left", va="bottom", color=MUTED, fontsize=7.5)
    a.set_ylim(-2, top)
    a.set_ylabel("Site export (kW)")
    a.set_title("Site: export against the CSIP-AUS export limit", loc="left", fontsize=11.5, color=INK, pad=8)
    a.legend(loc="upper right", frameon=False, fontsize=8.5, bbox_to_anchor=(1.0, 0.72))

    # Panel B: DER output against setMaxW.
    b.axhline(d["setMaxW_w"] / 1000, color=ORANGE, linewidth=1, linestyle=(0, (2, 2)))
    b.text(x1, d["setMaxW_w"] / 1000 + 0.5, "setMaxW reported: 35 kW", ha="right", va="bottom", color=INK2, fontsize=8.5)
    dx, dy = steps(der, der[-1][0] + win)
    b.plot(dx, dy, color=ORANGE, linewidth=2.2, label="DER output: solar + V2G EV (ODE)")
    b.set_ylim(-1, 39)
    b.set_ylabel("DER output (kW)")
    b.set_title("DER: output against the 35 kW setMaxW", loc="left", fontsize=11.5, color=INK, pad=8)
    b.legend(loc="upper right", frameon=False, fontsize=8.5, bbox_to_anchor=(1.0, 0.8))
    b.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 2)))
    b.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    b.set_xlim(x0, x1)
    b.set_xlabel("Time, 20 October 2026 (AEDT). Thin vertical lines: ODE's Started responses")
    fig.text(0.01, 0.005, "Readings: ODE's 60 s MirrorMeterReadings to Cactus. Limits: Cactus run timeline, 20 s steps.",
             color=MUTED, fontsize=8)
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"gen11-chart.{ext}", dpi=150, facecolor=SURFACE, bbox_inches="tight")


if __name__ == "__main__":
    main()
