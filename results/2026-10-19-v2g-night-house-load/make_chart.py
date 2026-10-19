"""Render the night-time V2G TxProfile chart from data.json.

Two panels on a shared AEDT time axis: the EV charger (requested, dispatched
and CSMS-measured power) and the site (net grid power from the site model at
the measured EV power) against the CSIP-AUS limits. Run from this folder:

    python3 make_chart.py
"""
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DAY = "2026-10-19 "
SURFACE, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"


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
    p, lim, sm = d["profile"], d["network_constraint"], d["site_model"]
    x0, x1 = t("20:55:50"), t("21:02:30")
    end = t(p["after_test"]["start"])
    measured = [(t(h), w) for h, w in d["csms_measured_ev_power_w"]]
    load = sm["house_load_w"] + sm["cactus_test_load_w"] - sm["pv_w"]
    site_pts = [(x, (load + w) / 1000) for x, w in measured]

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
        for s in d["bridge_sends"]:
            ax.axvline(t(s), color=GRID, linewidth=0.8, zorder=0)

    # Panel A: EV charger.
    req = [(t(s["start"]), s["requested_w"] / 1000) for s in p["steps"]]
    # Before the test the bridge's import-mode profile (sent at the transaction start) is in force.
    disp = [(t(d["events"]["transaction_started"]), p["after_test"]["dispatched_w"] / 1000)]
    disp += [(t(s["start"]), s["dispatched_w"] / 1000) for s in p["steps"]]
    disp.append((end, p["after_test"]["dispatched_w"] / 1000))
    a.plot(*steps(req, end), color=ORANGE, linewidth=2, linestyle=(0, (5, 3)), label="Requested setpoint")
    a.plot(*steps(disp, t("21:02:00")), color=BLUE, linewidth=2.2, label="Dispatched setpoint (clamped to site headroom)")
    a.plot(*steps([(x, w / 1000) for x, w in measured], x1), color=AQUA, linewidth=1.4, alpha=0.9)
    a.plot([x for x, _ in measured], [w / 1000 for _, w in measured], "o", color=AQUA, markersize=6,
           markeredgecolor=SURFACE, markeredgewidth=1.5, label="CSMS-measured EV power (MeterValues)")
    dh, ch = d["dispatch"]["discharge_headroom_w"], d["dispatch"]["charge_headroom_w"]
    for v, label, va in ((ch, f"Charge headroom {ch / 1000:.2f} kW", "bottom"),
                         (-dh, f"Discharge headroom {dh / 1000:.2f} kW (export limit + 0.95 x house load)", "top"),
                         (-d["dispatch"]["discharge_headroom_before_change_w"], "Before the house-load credit: 18.00 kW", "bottom")):
        a.axhline(v / 1000, color=INK2 if "Before" not in label else MUTED, linewidth=1, linestyle=(0, (2, 2)))
        a.text(t("21:01:20") if va == "bottom" and "Before" not in label else x1, v / 1000 + (0.5 if va == "bottom" else -0.5), label, ha="right", va=va,
               color=INK2 if "Before" not in label else MUTED, fontsize=8.5)
    a.set_ylim(-24, 26)
    a.set_ylabel("EV charger power (kW)\n+ charge, - discharge")
    a.set_title("EV charger: requested, dispatched and measured", loc="left", fontsize=11.5, color=INK, pad=26)
    a.legend(loc="lower left", frameon=False, fontsize=8.5, ncol=3, bbox_to_anchor=(0.0, 0.99), handlelength=2.2)

    # Panel B: site.
    b.axhspan(-lim["opModExpLimW"] / 1000, lim["opModImpLimW"] / 1000, color=BLUE, alpha=0.06, zorder=0, linewidth=0)
    for v, label, va in ((lim["opModImpLimW"] / 1000, "Import limit 18 kW (DERC2)", "top"),
                         (-lim["opModExpLimW"] / 1000, "Export limit 18 kW (DERC2)", "bottom")):
        b.axhline(v, color=INK2, linewidth=1, linestyle=(0, (2, 2)))
        b.text(t("20:59:25") if va == "top" else x1, v + (-0.6 if va == "top" else 0.6), label, ha="right", va=va, color=INK2, fontsize=9)
    b.plot(*steps(site_pts, x1), color=BLUE, linewidth=2.2, label="Site grid power (+ import, - export)")
    b.set_ylim(-22, 22)
    b.set_ylabel("Power (kW)")
    b.set_title("Site: grid power against the CSIP-AUS limits (site model, no solar)", loc="left",
                fontsize=11.5, color=INK, pad=8)
    b.legend(loc="lower right", frameon=False, fontsize=9, bbox_to_anchor=(1.0, 0.18))
    b.xaxis.set_major_locator(mdates.MinuteLocator())
    b.xaxis.set_minor_locator(mdates.SecondLocator(bysecond=[30]))
    b.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    b.set_xlim(x0, x1)
    b.set_xlabel("Time, 19 October 2026 (AEDT). Thin vertical lines: bridge profile sends")
    fig.text(0.01, 0.005, "Site values: site model at the measured EV power (mean values, before the +/-5% variation). "
             "House load 1 kW; no solar at night.", color=MUTED, fontsize=8)
    for ext in ("png", "svg"):
        fig.savefig(HERE / f"v2g-night-chart.{ext}", dpi=150, facecolor=SURFACE, bbox_inches="tight")


if __name__ == "__main__":
    main()
