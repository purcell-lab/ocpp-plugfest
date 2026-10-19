"""Render the network-constrained V2G TxProfile chart from data.json.

Two panels on a shared AEDT time axis: the EV charger (requested, dispatched
and CSMS-measured power) and the site (net grid power and solar output from
the site model at the measured EV power) against the CSIP-AUS limits. Run
from this folder:

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
DAY = "2026-10-19 "
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
NO_PROFILE = "#efeeea"


def t(hms):
    return datetime.fromisoformat(DAY + hms)


def steps(points, until):
    xs, ys = [], []
    for i, (x, y) in enumerate(points):
        nxt = points[i + 1][0] if i + 1 < len(points) else until
        xs += [x, nxt]
        ys += [y, y]
    return xs, ys


def site(load, ev, pv_avail, limit_exp):
    cap = load + (limit_exp + ev) / 1.05
    pv = min(pv_avail, 15000, cap)
    return load + ev - pv, pv


def main():
    d = json.loads((HERE / "data.json").read_text())
    p, lim = d["profile"], d["network_constraint"]
    sent = t(p["sent_at"])
    end = sent + timedelta(seconds=p["duration_s"])
    x0, x1 = t("14:39:50"), t("14:47:20")
    measured = [(t(h), w) for h, w in d["csms_measured_ev_power_w"]]
    forecast = [(t(h), w) for h, w in d["site_model"]["pv_forecast_w"]]
    load = d["site_model"]["house_load_w"]

    # Site model at each change of EV power or forecast.
    changes = sorted({x for x, _ in measured} | {x for x, _ in forecast if x >= x0})
    site_pts, pv_pts = [], []
    for x in changes:
        ev = [w for mx, w in measured if mx <= x][-1]
        fc = [w for fx, w in forecast if fx <= x][-1]
        s, pv = site(load, ev, fc, lim["opModExpLimW"])
        site_pts.append((x, s / 1000))
        pv_pts.append((x, pv / 1000))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, (a, b) = plt.subplots(2, 1, figsize=(10, 7.2), sharex=True, facecolor=SURFACE,
                               gridspec_kw={"height_ratios": [1.15, 1], "hspace": 0.32})
    for ax in (a, b):
        ax.set_facecolor(SURFACE)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.axhline(0, color=MUTED, linewidth=0.8)
        # Uncapped: no profile in force, the station charges at its 25 kW default.
        for s0, s1 in ((t("14:40:18"), sent + timedelta(seconds=5)), (t("14:46:33"), t("14:46:58"))):
            ax.axvspan(s0, s1, color=NO_PROFILE, zorder=0, linewidth=0)

    # Panel A: EV charger.
    req = [(sent + timedelta(seconds=s["startPeriod"]), s["requested_w"] / 1000) for s in p["steps"]]
    disp = [(sent + timedelta(seconds=s["startPeriod"]), s["dispatched_w"] / 1000) for s in p["steps"]]
    a.plot(*steps(req, end), color=ORANGE, linewidth=2, linestyle=(0, (5, 3)), label="Requested setpoint")
    a.plot(*steps(disp, end), color=BLUE, linewidth=2.2, label="Dispatched setpoint (clamped to site headroom)")
    mx, my = steps([(x, w / 1000) for x, w in measured], t("14:47:20"))
    a.plot(mx, my, color=AQUA, linewidth=1.4, alpha=0.9)
    a.plot([x for x, _ in measured], [w / 1000 for _, w in measured], "o", color=AQUA, markersize=6,
           markeredgecolor=SURFACE, markeredgewidth=1.5, label="CSMS-measured EV power (MeterValues)")
    a.axhline(p["limit_w"] / 1000, color=INK2, linewidth=1, linestyle=(0, (2, 2)))
    a.text(x1, p["limit_w"] / 1000 + 0.6, "Charge headroom 17.42 kW", ha="right", va="bottom", color=INK2, fontsize=9)
    a.text(x1, -1.2, "Discharge headroom 0 W", ha="right", va="top", color=INK2, fontsize=9)
    a.text(t("14:40:40"), 25.8, "No profile:\n25 kW default", ha="center", va="bottom", color=INK2, fontsize=8.5)
    a.text(t("14:46:45"), 25.8, "Profile\nexpired", ha="center", va="bottom", color=INK2, fontsize=8.5)
    a.set_ylim(-22, 30)
    a.set_ylabel("EV charger power (kW)\n+ charge, - discharge")
    a.set_title("EV charger: requested, dispatched and measured", loc="left", fontsize=11.5, color=INK, pad=8)
    a.legend(loc="lower right", frameon=False, fontsize=9)

    # Panel B: site.
    b.axhspan(-lim["opModExpLimW"] / 1000, lim["opModImpLimW"] / 1000, color="#2a78d6", alpha=0.06, zorder=0, linewidth=0)
    # Labels inside the permitted band, right of the last step and clear of the traces.
    for v, label, va in ((lim["opModImpLimW"] / 1000, "Import limit 4.5 kW (DERC1)", "top"),
                         (-lim["opModExpLimW"] / 1000, "Export limit 4.5 kW (DERC1)", "bottom")):
        b.axhline(v, color=INK2, linewidth=1, linestyle=(0, (2, 2)))
        b.text(t("14:46:25"), v + (-0.45 if va == "top" else 0.6), label, ha="right", va=va, color=INK2, fontsize=9)
    b.plot(*steps(site_pts, t("14:47:20")), color=BLUE, linewidth=2.2, label="Site grid power (+ import, - export)")
    b.plot(*steps(pv_pts, t("14:47:20")), color=ORANGE, linewidth=2, label="Solar output (curtailed)")
    b.set_ylim(-8, 18)
    b.set_ylabel("Power (kW)")
    b.set_title("Site: grid power and solar against the CSIP-AUS limits (site model)", loc="left",
                fontsize=11.5, color=INK, pad=8)
    b.legend(loc="upper right", frameon=False, fontsize=9)
    b.xaxis.set_major_locator(mdates.MinuteLocator())
    b.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=[30]))
    b.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    b.set_xlim(x0, x1)
    b.set_xlabel("Time, 19 October 2026 (AEDT)")
    fig.text(0.01, 0.005, "Site values: site model at the measured EV power (mean values, before the +/-5% variation). "
             "House load 1 kW; solar from the Open-Meteo forecast.", color=MUTED, fontsize=8)
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"v2g-constrained-chart.{ext}", dpi=150, facecolor=SURFACE, bbox_inches="tight")


if __name__ == "__main__":
    main()
