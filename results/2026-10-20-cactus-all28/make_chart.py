"""Render the Cactus ALL-28 run 75360 chart from data.json.

Top: the whole run on an AEDT time axis. It shows:
- the export limit Cactus set (the active DERControl, else the default);
- ODE's live, ramped export limit;
- site export as ODE posted it (60 s averages);
- the V2G EV's discharge as CitrineOS measured it.

Bottom: the three ramps, zoomed in. Each shows ODE's ramped limit, the EV's
headroom under it (the limit less solar's share, as the bridge works it out)
and the EV's discharge.

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
HOUSE = 1000


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


def solar_at(d, x):
    s = d["solar_forecast_w"][0][1]
    for h, w in d["solar_forecast_w"]:
        if t(h) <= x:
            s = w
    return s


def main():
    d = json.loads((HERE / "data.json").read_text())
    x0, x1 = t("09:28:30"), t("09:51:00")
    win = timedelta(seconds=60)
    target = [(t(h), w / 1000) for h, w in [("09:28:59", 0), ("09:29:28", 70000), ("09:32:29", 10500), ("09:35:31", 3500),
                                            ("09:38:31", 17500), ("09:43:35", 0), ("09:47:34", 10500)]]
    ode = [(t(h), w / 1000) for h, w in d["ode_export_limit_w"] if w >= 0]
    ev = [(t(h), -w / 1000) for h, w in d["ev_power_w"] if w is not None]
    site = [(t(h) - win, -w / 1000) for h, w in d["ode_site_net_w"]]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig = plt.figure(figsize=(11, 8.6), facecolor=SURFACE)
    gs = fig.add_gridspec(2, 3, height_ratios=[1.25, 1], hspace=0.42, wspace=0.18)
    a = fig.add_subplot(gs[0, :])
    style(a)
    top = 32
    tx, ty = steps(target, x1)
    a.plot(tx, [min(y, top - 1) for y in ty], color=MUTED, linewidth=1.2, linestyle=(0, (3, 2)), label="Export limit Cactus set")
    a.annotate("70 kW", xy=(t("09:31:40"), top - 1), xytext=(t("09:31:40"), top - 5), ha="center", color=INK2,
               fontsize=8.5, arrowprops={"arrowstyle": "->", "color": INK2, "lw": 0.8})
    ox, oy = steps(ode, x1)
    a.plot(ox, [min(y, top - 1) for y in oy], color=INK2, linewidth=1.4, label="ODE's ramped export limit")
    sx, sy = steps(site, site[-1][0] + win)
    a.plot(sx, sy, color=BLUE, linewidth=2.2, label="Site export (ODE, 60 s averages)")
    ex, ey = steps(ev, x1)
    a.plot(ex, ey, color=ORANGE, linewidth=1.8, label="EV discharge (CitrineOS)")
    for n, (h, label) in enumerate([("09:29:28", "PRE-\nCONDITION"), ("09:32:29", "DERC1\n30 %"), ("09:35:31", "DERC2\n10 %"),
                     ("09:38:31", "DERC3\n50 %, 60 s"), ("09:42:33", "setGradW\n1 %/s"), ("09:43:35", "cancel\n→ 0 W"),
                     ("09:47:34", "DERC4\n30 %")]):
        a.axvline(t(h), color=GRID, linewidth=0.8, zorder=0)
        a.text(t(h) + timedelta(seconds=8), top - 0.5 - (3.2 if n == 5 else 0), label, ha="left", va="top", color=MUTED, fontsize=7.5)
    a.set_xlim(x0, x1)
    a.set_ylim(-1, top)
    a.set_ylabel("kW")
    a.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, 2)))
    a.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    a.set_title("ALL-28 run 75360: export limits, site export and the V2G EV", loc="left", fontsize=11.5, pad=8)
    a.legend(loc="center right", frameon=False, fontsize=8.5, bbox_to_anchor=(1.0, 0.45))

    zooms = [("DERC3: 10 % → 50 %, rampTms 60 s", "09:38:20", "09:39:55"),
             ("Cancel: 50 % → 0 W at setGradW 1 %/s", "09:43:25", "09:45:00"),
             ("DERC4: 0 W → 30 % at 1 %/s", "09:47:25", "09:49:00")]
    for i, (title, z0, z1) in enumerate(zooms):
        b = fig.add_subplot(gs[1, i])
        style(b)
        z0, z1 = t(z0), t(z1)
        pts = [p for p in ode if z0 - timedelta(minutes=10) <= p[0] <= z1]
        bx, by = steps(pts, z1)
        b.plot(bx, by, color=INK2, linewidth=1.4, label="ODE's ramped limit")
        head = [(x, max(y - (1.05 * solar_at(d, x) - 0.95 * HOUSE) / 1000, 0)) for x, y in pts]
        hx, hy = steps(head, z1)
        b.plot(hx, hy, color=ORANGE, linewidth=1, linestyle=(0, (1, 1.5)), label="EV headroom (limit less solar's share)")
        evz = [p for p in ev if z0 - timedelta(minutes=10) <= p[0] <= z1]
        vx, vy = steps(evz, z1)
        b.plot(vx, vy, color=ORANGE, linewidth=2, label="EV discharge")
        b.set_xlim(z0, z1)
        b.set_ylim(-0.5, 19)
        b.xaxis.set_major_locator(mdates.SecondLocator(bysecond=[0, 30]))
        b.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        b.tick_params(axis="x", labelsize=7.5)
        b.set_title(title, loc="left", fontsize=9.5, pad=6)
        if i == 0:
            b.set_ylabel("kW")
            b.legend(loc="upper left", frameon=False, fontsize=7.5)
    fig.text(0.01, 0.005, "Times AEDT, 20 October 2026. ODE's limit: lab helper fed from ODE's limits/csipAus (about 1 s). "
             "EV: CitrineOS meter values (about 5 s). Site: ODE's 60 s MirrorMeterReadings to Cactus.",
             color=MUTED, fontsize=7.5)
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"all28-chart.{ext}", dpi=150, facecolor=SURFACE, bbox_inches="tight")


if __name__ == "__main__":
    main()
