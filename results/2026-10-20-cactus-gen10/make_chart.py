"""Render the Cactus GEN-10 run 75351 chart from data.json.

Two panels on a shared AEDT time axis:
- the site: export as ODE posted it to Cactus, against the export limit in force
  (DERP 1 control, else DERP 6 control, else the DERP 1 default);
- the DER (solar plus the V2G EV, as ODE posted it) against the generation limit
  and the 10 kW setMaxW ODE reported during the run.
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
SHADE = "#efeeea"


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
    x0, x1 = t("07:44:00"), t("08:43:00")
    # ODE labels each 60 s average with the end of its window (see README), so each value is
    # drawn over the minute before its timestamp.
    win = timedelta(seconds=60)
    site = [(t(h) - win, -w / 1000) for h, w in d["ode_site_net_w"]]
    der = [(t(h) - win, w / 1000) for h, w in d["ode_der_net_w"]]
    exp, gen = [], []
    for r in d["cactus_limits_w"]:
        v = next((r[k] for k in ("derp1_exp", "derp6_exp", "default_exp") if r[k] is not None), None)
        g = [r[k] for k in ("derp1_gen", "derp6_gen") if r[k] is not None]
        exp.append((t(r["t"]), None if v is None else v / 1000))
        gen.append((t(r["t"]), min(g) / 1000 if g else None))
    started = []
    for s in d["steps"]:
        if s[4].endswith("RESPONSE-STARTED"):
            x, name = t(s[0]), "DERC" + s[4].split("-")[2]
            # Controls started within a few seconds of each other share one label.
            if started and (x - started[-1][0]).total_seconds() < 15:
                started[-1] = (started[-1][0], started[-1][1] + "/" + name[4:])
            else:
                started.append((x, name))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, (a, b) = plt.subplots(2, 1, figsize=(11, 7.6), sharex=True, facecolor=SURFACE,
                               gridspec_kw={"height_ratios": [1.2, 1], "hspace": 0.3})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        # DERC 4: opModConnect false, opModGenLimW 0, from its Started to its Completed response.
        ax.axvspan(t("08:14:05"), t("08:19:01"), color=SHADE, zorder=0, linewidth=0)
        for x, _ in started:
            ax.axvline(x, color=GRID, linewidth=0.8, zorder=0)

    # Panel A: site export against the export limit.
    ex, ey = steps([p for p in exp if p[1] is not None], x1)
    a.plot(ex, ey, color=INK2, linewidth=1.3, linestyle=(0, (3, 2)), label="Export limit in force")
    sx, sy = steps(site, site[-1][0] + win)
    a.plot(sx, sy, color=BLUE, linewidth=2.2, label="Site export (ODE, 60 s averages)")
    for x, label in started:
        a.text(x, 22.3, label, rotation=90, ha="right", va="top", color=MUTED, fontsize=7.5)
    a.text(t("08:16:33"), 16.5, "Disconnected\n(DERC4)", ha="center", va="top", color=INK2, fontsize=8.5)
    a.set_ylim(-3, 22.5)
    a.set_ylabel("Site export (kW)\n- import")
    a.set_title("Site: export against the CSIP-AUS export limit", loc="left", fontsize=11.5, color=INK, pad=8)
    a.legend(loc="lower left", frameon=False, fontsize=8.5, bbox_to_anchor=(0.115, 0.2))

    # Panel B: DER output against the generation limit and setMaxW.
    gx, gy = steps([p for p in gen if p[1] is not None], x1)
    b.axhline(d["setMaxW_w"] / 1000, color=ORANGE, linewidth=1, linestyle=(0, (2, 2)))
    b.text(x1, d["setMaxW_w"] / 1000 + 0.3, "setMaxW reported: 10 kW", ha="right", va="bottom", color=INK2, fontsize=8.5)
    dx, dy = steps(der, der[-1][0] + win)
    b.plot(dx, dy, color=ORANGE, linewidth=2.2, label="DER output: solar + V2G EV, as ODE posted it")
    b.set_ylim(-1, 16)
    b.set_ylabel("DER output (kW)")
    b.set_title("DER: output against the 10 kW setMaxW ODE reported", loc="left", fontsize=11.5, color=INK, pad=8)
    b.legend(loc="upper left", frameon=False, fontsize=9)
    b.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 5)))
    b.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    b.set_xlim(x0, x1)
    b.set_xlabel("Time, 20 October 2026 (AEDT). Thin vertical lines: ODE's Started responses")
    fig.text(0.01, 0.005, "Readings: ODE's 60 s MirrorMeterReadings to Cactus (site net and DER net). Limits: Cactus "
             "run timeline, 20 s steps.", color=MUTED, fontsize=8)
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"gen10-chart.{ext}", dpi=150, facecolor=SURFACE, bbox_inches="tight")


if __name__ == "__main__":
    main()
