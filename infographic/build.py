#!/usr/bin/env python3
"""Generate the OCPP Plugfest graphics (infographic + README assets) as SVG."""
import base64, os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.dirname(os.path.abspath(__file__))

# ---------- brand tokens ----------
TEAL = "#0f6e6e"
TEAL_D = "#0a4f4f"
TEAL_DD = "#083f3f"
TEAL_L = "#d7ebe8"
GOLD = "#d2a55c"
GOLD_T = "#8a6420"     # gold for text on cream (4.99:1)
GOLD_L = "#f3e2c0"
CREAM = "#fff6e5"
PAPER = "#fffcf6"
INK = "#1b1b1b"
GREY = "#5a5a5a"
RULE = "#e7dcc6"
GRID = "#ebe2cf"
CHG = "#2e8540"        # charge / import (validated pair, light on cream)
DIS = "#2a6fc9"        # discharge / export
ZERO = "#8a8a8a"

FONT = "Inter, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


CREST200 = b64(os.path.join(WORK, "crest200.png"))
CREST120 = b64(os.path.join(WORK, "crest120.png"))


def T(x, y, s, size=16, weight=400, fill=INK, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{(" " + extra) if extra else ""}>{escape(s)}</text>')


def TS(x, y, parts, size=16, anchor="start", extra=""):
    """text with tspans: parts = [(str, weight, fill)]"""
    sp = "".join(f'<tspan font-weight="{w}" fill="{c}">{escape(s)}</tspan>' for s, w, c in parts)
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}"{(" " + extra) if extra else ""}>{sp}</text>'


# ---------- icons (64x64, stroke = currentColor, accent gold) ----------
SW = 'fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"'
ICONS = {
    # transmission tower
    "tower": f'''<g {SW}><path d="M32 6 L18 58 M32 6 L46 58 M10 18 H54 M16 31 H48 M25.5 18 L39 31 M38.5 18 L25 31 M21.5 45 H42.5 M24.5 31 L42 45 M39.5 31 L22 45 M21.5 45 L46 58 M42.5 45 L18 58"/></g>
<g fill="{GOLD}"><circle cx="10" cy="18" r="3.2"/><circle cx="54" cy="18" r="3.2"/><circle cx="16" cy="31" r="3.2"/><circle cx="48" cy="31" r="3.2"/></g>''',
    # dynamic operating envelope
    "envelope": f'''<path d="M9 8 V55 H57" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity=".55"/>
<path d="M12 20 H25 V30 H38 V16 H54" fill="none" stroke="{GOLD}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M12 46 C19 40 22 34 25 34 C30 34 33 38 38 36 C44 33 47 25 54 24" {SW}/>
<path d="M12 46 C19 40 22 34 25 34 C30 34 33 38 38 36 C44 33 47 25 54 24 V55 H12 Z" fill="currentColor" opacity=".12"/>''',
    # home energy management
    "home": f'''<g {SW}><path d="M7 31 L32 9 L57 31"/><path d="M14 26 V56 H50 V26"/>
<path d="M32 36 L23 46 M32 36 L41 46 M32 36 V27"/></g>
<g fill="{GOLD}"><circle cx="32" cy="36" r="5"/><circle cx="23" cy="47" r="3.6"/><circle cx="41" cy="47" r="3.6"/><circle cx="32" cy="26" r="3.6"/></g>''',
    # CSMS server stack
    "server": f'''<g {SW}><rect x="10" y="8" width="44" height="13" rx="4"/><rect x="10" y="26" width="44" height="13" rx="4"/><rect x="10" y="44" width="44" height="13" rx="4"/>
<path d="M17 14.5 H31 M17 32.5 H31 M17 50.5 H31"/></g>
<g fill="{GOLD}"><circle cx="46" cy="14.5" r="3"/><circle cx="46" cy="32.5" r="3"/><circle cx="46" cy="50.5" r="3"/></g>''',
    # charging station
    "charger": f'''<g {SW}><rect x="10" y="7" width="27" height="49" rx="5"/><path d="M6 57 H41"/>
<path d="M37 23 H43 C46.5 23 48 25 48 28 V43 C48 46 50 48 53 48"/><path d="M53 41 V55"/></g>
<rect x="15.5" y="13" width="16" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="2.5"/>
<path d="M25.2 15 L19.6 21.4 H24 L22.4 26 L28.2 19.6 H23.8 Z" fill="{GOLD}"/>
<rect x="50" y="40" width="9" height="11" rx="2.5" fill="{GOLD}"/>''',
    # EV with bidirectional arrows
    "ev": f'''<g {SW}><path d="M6 46 V38 L13 35.5 L20.5 26 H42 L50.5 35.5 L58 37.5 V46 H52"/><path d="M38 46 H26"/><path d="M12 46 H6"/>
<path d="M22.5 35 H48"/></g>
<g fill="none" stroke="currentColor" stroke-width="3"><circle cx="19" cy="47" r="6"/><circle cx="45" cy="47" r="6"/></g>
<g fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M19 10 H45 M24 5 L19 10 L24 15 M40 5 L45 10 L40 15"/></g>''',
    # export clip during V2G discharge (car pushes power up to a limit)
    "export": f'''<g {SW}><path d="M8 54 V49 L13 47 L18 41 H34 L39 47 L44 48.5 V54"/></g>
<path d="M50 52 V24" fill="none" stroke="{DIS}" stroke-width="3.5" stroke-linecap="round"/>
<path d="M43.5 30 L50 23.5 L56.5 30" fill="none" stroke="{DIS}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M8 15 H58" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>
<path d="M8 26 C16 26 18 15 24 15 H36" fill="none" stroke="{DIS}" stroke-width="2.5" stroke-linecap="round" opacity=".7"/>''',
    # import clip during charging (grid pushes power down into car, limited)
    "import": f'''<g {SW}><path d="M8 54 V49 L13 47 L18 41 H34 L39 47 L44 48.5 V54"/></g>
<path d="M50 22 V50" fill="none" stroke="{CHG}" stroke-width="3.5" stroke-linecap="round"/>
<path d="M43.5 44 L50 50.5 L56.5 44" fill="none" stroke="{CHG}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M8 15 H58" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>
<path d="M8 32 C16 32 18 15 24 15 H36" fill="none" stroke="{CHG}" stroke-width="2.5" stroke-linecap="round" opacity=".7"/>''',
    # site load clip
    "load": f'''<g {SW}><path d="M8 33 L32 12 L56 33"/><path d="M15 28 V56 H49 V28"/></g>
<path d="M4 38 H60" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>
<path d="M22 56 V46 M32 56 V40 M42 56 V44" stroke="currentColor" stroke-width="5" stroke-linecap="round" opacity=".55"/>''',
    # 1-minute MSL / LOR event
    "clock": f'''<g {SW}><circle cx="32" cy="36" r="21"/><path d="M27 8 H37 M32 8 V15 M50 17 L54 13"/></g>
<path d="M32 36 L32 21" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>
<path d="M32 21 A15 15 0 0 1 47 36 L32 36 Z" fill="{GOLD}" opacity=".35"/>
<circle cx="32" cy="36" r="3.5" fill="currentColor"/>''',
    # local network congestion: distribution pole + transformer + warning
    "congestion": f'''<g {SW}><path d="M22 6 V58 M10 13 H34 M13 13 V9 M31 13 V9 M15 58 H29"/>
<rect x="24" y="22" width="11" height="17" rx="3"/></g>
<path d="M47 27 L59 49 H35 Z" fill="{GOLD}" stroke="{GOLD}" stroke-width="2.5" stroke-linejoin="round"/>
<path d="M47 34 V41" stroke="{INK}" stroke-width="3" stroke-linecap="round"/><circle cx="47" cy="45.3" r="1.8" fill="{INK}"/>''',
    # price signal (AEMO spot)
    "price": f'''<g {SW}><circle cx="20" cy="20" r="13"/></g>
<text x="20" y="26.5" font-size="18" font-weight="700" fill="currentColor" text-anchor="middle">$</text>
<path d="M6 54 L18 50 L26 52 L34 44 L40 47 L46 24 L52 46 L59 42" fill="none" stroke="{GOLD}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>''',
    # OpenADR 3.1 VTN: price tag broadcasting a signal
    "vtn": f'''<g {SW}><path d="M7 33 L33 7 H52.5 Q57 7 57 11.5 V31 L31 57 Z"/></g>
<circle cx="47.5" cy="16.5" r="3.6" fill="{GOLD}"/>
<text x="33" y="40.5" font-size="20" font-weight="800" fill="currentColor" text-anchor="middle">$</text>
<g fill="none" stroke="{GOLD}" stroke-width="3.2" stroke-linecap="round"><path d="M12 21.5 A10.5 10.5 0 0 1 21.5 12"/><path d="M4.5 21 A17 17 0 0 1 21 4.5"/></g>''',
    "check": f'''<path d="M18 33 L28 43 L47 22" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>''',
}


def defs(*names, extra=""):
    syms = "".join(f'<symbol id="i-{n}" viewBox="0 0 64 64">{ICONS[n]}</symbol>' for n in names)
    return f"<defs>{syms}{extra}</defs>"


def icon(name, x, y, size, color=TEAL):
    return f'<use href="#i-{name}" x="{x}" y="{y}" width="{size}" height="{size}" color="{color}"/>'


def svg_open(w, h, title, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-labelledby="t d" font-family="{FONT}">'
            f'<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>')


def arrow(x1, y, x2, color=GOLD, w=3.5):
    return (f'<path d="M{x1} {y} H{x2 - 2}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{x2 - 11} {y - 7} L{x2} {y} L{x2 - 11} {y + 7}" fill="none" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


# ---------- chain data ----------
CHAIN = [
    ("tower", "Network operator", "CSIP-AUS server", "ANU BSGIP Cactus", "v1.2 test harness"),
    ("envelope", "Open Dynamic", "Export (ODE)", "CSIP-AUS client", "dynamic envelopes"),
    ("home", "Home Assistant", "EEMS", "Green · OpenADR VEN", "bridge + CitrineOS-HA"),
    ("server", "CitrineOS", "CSMS", "OCPP 2.1 / 2.0.1 / 1.6", "open-source CSMS"),
    ("charger", "EVerest →", "Plugfest stations", "charging stations", "validate profiles"),
    ("ev", "Electric vehicle", "V2G", "ISO 15118-20 EV", "charge + · discharge −"),
]
LINKS = [
    ("SEP2 · IEEE 2030.5", "CSIP-AUS"),
    ("MQTT", "limits"),
    ("REST", "CitrineOS API"),
    ("OCPP 2.1", "SetChargingProfile"),
    ("ISO 15118-20", "DC_BPT"),
]

PRICE_SRC = ("vtn", "OpenADR 3.1 VTN", "price server", "AU tariff events · 5/30-min")
PRICE_LINK = ("OpenADR 3.1", "PRICE · EXPORT_PRICE")


def chain(x0, y0, width, tile_w=200, tile_h=236, compact=False, f1=20, f2=15):
    """Six tiles with arrows; link pills below arrows. Returns svg string and height."""
    n = len(CHAIN)
    gap = (width - n * tile_w) / (n - 1)
    out = []
    icon_sz = 64 if not compact else 54
    for i, (ic, t1, t2, s1, s2) in enumerate(CHAIN):
        x = x0 + i * (tile_w + gap)
        hl = i in (2,)  # Purcell's EEMS in the middle gets the gold ring
        out.append(f'<rect x="{x}" y="{y0}" width="{tile_w}" height="{tile_h}" rx="18" fill="#ffffff" '
                   f'stroke="{GOLD if hl else RULE}" stroke-width="{3 if hl else 1.5}"/>')
        cx = x + tile_w / 2
        out.append(f'<circle cx="{cx}" cy="{y0 + 58}" r="{40 if not compact else 34}" fill="{CREAM}"/>')
        out.append(icon(ic, cx - icon_sz / 2, y0 + 58 - icon_sz / 2, icon_sz))
        ty = y0 + (124 if not compact else 114)
        out.append(T(cx, ty, t1, f1, 700, INK, "middle"))
        out.append(T(cx, ty + f1 * 1.2, t2, f1, 700, INK, "middle"))
        if not compact:
            out.append(f'<path d="M{cx - 22} {ty + 44 - (20 - f1) * 1.6} H{cx + 22}" stroke="{GOLD}" stroke-width="2.5" stroke-linecap="round"/>')
            out.append(T(cx, ty + 72 - (20 - f1) * 1.6, s1, f2, 500, GREY, "middle"))
            out.append(T(cx, ty + 72 - (20 - f1) * 1.6 + f2 * 1.4, s2, f2, 400, GREY, "middle"))
        else:
            out.append(T(cx, ty + 50, s1, 14, 500, GREY, "middle"))
    # arrows + pills
    for i, (l1, l2) in enumerate(LINKS):
        xa = x0 + (i + 1) * tile_w + i * gap
        xb = xa + gap
        ay = y0 + 58
        out.append(arrow(xa + 8, ay, xb - 8))
    return "".join(out), gap


def link_pills(x0, y, width, tile_w, gap, h=58, size1=16, size2=14, pw=214):
    out = []
    for i, (l1, l2) in enumerate(LINKS):
        cxl = x0 + (i + 1) * tile_w + i * gap + gap / 2
        main = i == 3
        fill = TEAL if main else CREAM
        stroke = TEAL if main else GOLD
        c1 = "#ffffff" if main else TEAL_D
        c2 = GOLD_L if main else GREY
        out.append(f'<path d="M{cxl} {y - 40} V{y}" stroke="{GOLD}" stroke-width="2" stroke-dasharray="0" opacity=".9"/>')
        out.append(f'<circle cx="{cxl}" cy="{y - 40}" r="4" fill="{GOLD}"/>')
        out.append(f'<rect x="{cxl - pw / 2}" y="{y}" width="{pw}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        out.append(T(cxl, y + h / 2 - 3, l1, size1, 700, c1, "middle"))
        out.append(T(cxl, y + h / 2 + 17, l2, size2, 500, c2, "middle"))
    return "".join(out)


def price_lane(x, y, w, h, hx, top, f1=20, f2=15, r=34, icon_sz=52,
               pw=200, ph=58, ps1=16, ps2=14):
    """Second input lane: OpenADR VTN tile, then an arrow (with pill) that turns up into the
    bottom of the Home Assistant tile at x=hx, ending at y=top."""
    ic, t1, s1, s2 = PRICE_SRC
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#ffffff" stroke="{RULE}" stroke-width="1.5"/>']
    cx, cy = x + 14 + r, y + h / 2
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{CREAM}"/>')
    o.append(icon(ic, cx - icon_sz / 2, cy - icon_sz / 2, icon_sz))
    tx = cx + r + 16
    blk = f1 * 0.72 + 2 * f2 * 1.45
    b0 = cy - blk / 2 + f1 * 0.72
    o.append(T(tx, b0, t1, f1, 700, INK))
    o.append(T(tx, b0 + f2 * 1.45, s1, f2, 500, GREY))
    o.append(T(tx, b0 + f2 * 2.9, s2, f2, 400, GREY))
    # arrow: right, round the corner, up into Home Assistant
    xa = x + w + 8
    rr = 16
    o.append(f'<path d="M{xa} {cy} H{hx - rr} Q{hx} {cy} {hx} {cy - rr} V{top + 2}" fill="none" stroke="{GOLD}" '
             f'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<path d="M{hx - 7} {top + 11} L{hx} {top} L{hx + 7} {top + 11}" fill="none" stroke="{GOLD}" '
             f'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
    pcx = (xa + hx - rr) / 2
    l1, l2 = PRICE_LINK
    o.append(f'<rect x="{pcx - pw / 2}" y="{cy - ph / 2}" width="{pw}" height="{ph}" rx="{ph / 2}" fill="{CREAM}" stroke="{GOLD}" stroke-width="2"/>')
    o.append(T(pcx, cy - 3, l1, ps1, 700, TEAL_D, "middle"))
    o.append(T(pcx, cy + 17, l2, ps2, 500, GREY, "middle"))
    return "".join(o)


# ---------- V2G TxProfile chart ----------
STEPS = [(0, 60, 20), (60, 120, -20), (120, 180, 6), (180, 240, -5), (240, 300, 0)]
STEP_LBL = ["+20 kW", "−20 kW", "+6 kW", "−5 kW", "0 W"]


def setpoint(t):
    for a, b, v in STEPS:
        if a <= t < b:
            return v
    return 0


# Recorded CSMS MeterValues (5 s), seconds from the profile's startSchedule.
# Samples before 5 s still show the 25 kW drawn before the profile applied.
def _samples():
    import datetime as dt, json
    d = json.load(open(os.path.join(ROOT, "results/2026-10-17-v2g-txprofile/data.json")))
    t0 = dt.datetime.fromisoformat(d["profile"]["chargingSchedule"][0]["startSchedule"].replace("Z", "+00:00"))
    out = []
    for s in d["csms_meter_values"]["samples"]:
        t = (dt.datetime.fromisoformat(s["utc"].replace("Z", "+00:00")) - t0).total_seconds()
        if 5 <= t <= 300:
            out.append((round(t, 1), s["power_active_import_w"] / 1000))
    return out


SAMPLES = _samples()


def pol(v):
    return CHG if v > 0 else (DIS if v < 0 else ZERO)


def chart(x, y, w, h, surface=CREAM, fs=1.0, show_legend=True, note=True):
    """Step chart: dashed ink setpoint vs measured (polarity-coloured). Plot area inside x,y,w,h."""
    L, R, TOP, BOT = 74 * fs, 24 * fs, 16 * fs, 58 * fs
    px0, px1 = x + L, x + w - R
    py0, py1 = y + TOP, y + h - BOT
    ymax = 25.0
    sx = lambda t: px0 + (px1 - px0) * t / 300.0
    sy = lambda v: py0 + (py1 - py0) * (ymax - v) / (2 * ymax)
    o = []
    # polarity bands
    o.append(f'<rect x="{px0}" y="{py0}" width="{px1 - px0}" height="{sy(0) - py0}" fill="{CHG}" opacity=".045"/>')
    o.append(f'<rect x="{px0}" y="{sy(0)}" width="{px1 - px0}" height="{py1 - sy(0)}" fill="{DIS}" opacity=".045"/>')
    # grid
    for v in (-20, -10, 10, 20):
        o.append(f'<path d="M{px0} {sy(v)} H{px1}" stroke="{GRID}" stroke-width="1"/>')
        o.append(T(px0 - 12 * fs, sy(v) + 5 * fs, f"{v:+d}".replace("-", "−"), 14 * fs, 500, GREY, "end",
                   'font-variant-numeric="tabular-nums"'))
    o.append(T(px0 - 12 * fs, sy(0) + 5 * fs, "0", 14 * fs, 500, GREY, "end"))
    for t in (0, 60, 120, 180, 240, 300):
        o.append(f'<path d="M{sx(t)} {py0} V{py1}" stroke="{GRID}" stroke-width="1"/>')
        o.append(T(sx(t), py1 + 24 * fs, f"{t} s", 14 * fs, 500, GREY, "middle"))
    o.append(f'<path d="M{px0} {sy(0)} H{px1}" stroke="#b9ad97" stroke-width="1.5"/>')
    # axis titles
    o.append(T((px0 + px1) / 2, py1 + 50 * fs, "Seconds from start of the TxProfile (17 Oct 2026)", 14 * fs, 600, GREY, "middle"))
    o.append(T(x + 16 * fs, (py0 + py1) / 2, "Power (kW)", 14 * fs, 600, GREY, "middle",
               f'transform="rotate(-90 {x + 16 * fs} {(py0 + py1) / 2})"'))
    # in-plot polarity labels
    o.append(T(px1 - 26 * fs, py0 + 22 * fs, "+ charge (import)", 14 * fs, 700, INK, "end"))
    o.append(f'<circle cx="{px1 - 14 * fs}" cy="{py0 + 17 * fs}" r="{5 * fs}" fill="{CHG}"/>')
    o.append(T(px1 - 26 * fs, py1 - 12 * fs, "− discharge (export, V2G)", 14 * fs, 700, INK, "end"))
    o.append(f'<circle cx="{px1 - 14 * fs}" cy="{py1 - 17 * fs}" r="{5 * fs}" fill="{DIS}"/>')
    # measured washes
    segs = []
    for i, (t, v) in enumerate(SAMPLES):
        t2 = SAMPLES[i + 1][0] if i + 1 < len(SAMPLES) else 300
        segs.append((t, t2, v))
    for t1, t2, v in segs:
        if v != 0:
            yy, hh = (sy(v), sy(0) - sy(v)) if v > 0 else (sy(0), sy(v) - sy(0))
            o.append(f'<rect x="{sx(t1)}" y="{yy}" width="{sx(t2) - sx(t1)}" height="{hh}" fill="{pol(v)}" opacity="{.10 if v > 0 else .14}"/>')
    # setpoint (dashed ink)
    d = f"M{sx(0)} {sy(STEPS[0][2])}"
    for a, b, v in STEPS:
        d += f" V{sy(v)} H{sx(b)}"
    o.append(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{2 * fs}" stroke-dasharray="{7 * fs} {5 * fs}" stroke-linejoin="round"/>')
    # measured: step line segments coloured by polarity
    for i, (t1, t2, v) in enumerate(segs):
        o.append(f'<path d="M{sx(t1)} {sy(v)} H{sx(t2)}" stroke="{pol(v)}" stroke-width="{3 * fs}" stroke-linecap="round"/>')
        if i + 1 < len(segs) and segs[i + 1][2] != v:
            v2 = segs[i + 1][2]
            o.append(f'<path d="M{sx(t2)} {sy(v)} V{sy(v2)}" stroke="{pol(v2) if v2 else pol(v)}" stroke-width="{3 * fs}" stroke-linecap="round"/>')
    for t, v in SAMPLES:
        o.append(f'<circle cx="{sx(t)}" cy="{sy(v)}" r="{4 * fs}" fill="{pol(v)}" stroke="{surface}" stroke-width="{2 * fs}"/>')
    # step labels (one per step)
    for (a, b, v), lab in zip(STEPS, STEP_LBL):
        cx = sx((a + b) / 2)
        if v > 0:
            ly = sy(v) - 14 * fs
        elif v < 0:
            ly = sy(v) + 28 * fs
        else:
            ly = sy(0) - 14 * fs
        o.append(T(cx, ly, lab, 16 * fs, 800, INK, "middle"))
    if note:
        o.append(T(sx(92), sy(-20) - 14 * fs, "380 V × −52.6 A", 13 * fs, 500, GREY, "middle"))
    return "".join(o)


def chart_legend(x, y, fs=1.0):
    o = []
    o.append(f'<path d="M{x} {y} H{x + 34 * fs}" stroke="{INK}" stroke-width="{2 * fs}" stroke-dasharray="{7 * fs} {5 * fs}"/>')
    o.append(T(x + 44 * fs, y + 5 * fs, "OCPP 2.1 TxProfile setpoint (CentralSetpoint)", 14 * fs, 500, INK))
    x2 = x + 380 * fs
    o.append(f'<path d="M{x2} {y} H{x2 + 34 * fs}" stroke="{CHG}" stroke-width="{3 * fs}"/>')
    o.append(f'<circle cx="{x2 + 17 * fs}" cy="{y}" r="{4 * fs}" fill="{CHG}"/>')
    o.append(f'<path d="M{x2 + 40 * fs} {y} H{x2 + 74 * fs}" stroke="{DIS}" stroke-width="{3 * fs}"/>')
    o.append(f'<circle cx="{x2 + 57 * fs}" cy="{y}" r="{4 * fs}" fill="{DIS}"/>')
    o.append(T(x2 + 84 * fs, y + 5 * fs, "Charger meter (CSMS MeterValues, 5 s)", 14 * fs, 500, INK))
    return "".join(o)


# ---------- scenario + stats data ----------
SCEN = [
    ("export", "Export-limit clip", "during V2G discharge"),
    ("import", "Import-limit clip", "during charging"),
    ("load", "Load-limit clip", "site load envelope"),
    ("clock", "1-minute MSL / LOR", "short-notice events"),
    ("congestion", "Local congestion", "network constraint"),
    ("price", "Price events", "OpenADR 3.1 PRICE"),
]
STATS = [
    ("16/16", "LOA-11 import limits", "AC charger · run 74858"),
    ("16/16", "LOA-11 import limits", "DC V2G charger · run 74865"),
    ("±20 kW", "tracked exactly", "OCPP 2.1 CentralSetpoint"),
    ("±25 kW", "DC V2G rating", "ISO 15118-20 DC_BPT"),
    ("600 s", "schedule-ahead", "≤10 OCPP profile periods"),
    ("100%", "open source", "every component"),
]
AS = [
    ("SEP2", "via CSIP-AUS", "IEEE 2030.5 · AS 5385:2023", "Primary path", True),
    ("OCPP 2.1", "bidirectional EV charging", "SetChargingProfile · TxProfile", "Primary path", True),
    ("SunSpec Modbus 1.2", "inverters", "hybrid inverter", "Secondary path", False),
]
TIMING = [("≤5 s", "read / write"), ("≤30 s", "active-power limit"), ("≤15 s", "comms-loss fail-safe")]


def stat_cards(x0, y0, width, h, n=6, sizes=(46, 17, 14), bg="#ffffff"):
    gap = 18
    cw = (width - gap * (n - 1)) / n
    o = []
    for i, (big, l1, l2) in enumerate(STATS[:n]):
        x = x0 + i * (cw + gap)
        o.append(f'<rect x="{x}" y="{y0}" width="{cw}" height="{h}" rx="16" fill="{bg}" stroke="{RULE}" stroke-width="1.5"/>')
        o.append(f'<rect x="{x + 22}" y="{y0}" width="44" height="5" rx="2.5" fill="{GOLD}"/>')
        o.append(T(x + 22, y0 + 26 + sizes[0], big, sizes[0], 800, TEAL, "start", 'letter-spacing="-1"'))
        o.append(T(x + 22, y0 + 52 + sizes[0] + sizes[1] * 0.4, l1, sizes[1], 700, INK))
        o.append(T(x + 22, y0 + 52 + sizes[0] + sizes[1] * 0.4 + sizes[2] + 8, l2, sizes[2], 400, GREY))
    return "".join(o)


# ============================================================
#  INFOGRAPHIC 1600 x 2263
# ============================================================
def infographic():
    W, H = 1600, 2263
    M = 80
    CW = W - 2 * M
    o = [svg_open(W, H, "From grid signal to bidirectional charging profile",
                  "Open-source, standards-based chain: CSIP-AUS dynamic operating envelopes from the network operator "
                  "and OpenADR 3.1 price events both reach the Home Assistant EEMS, which sends one OCPP 2.1 "
                  "bidirectional charging profile to the charging station. OCA OCPP Plugfest & Conference Australia, "
                  "21-23 October 2026, Canberra.")]
    o.append(defs(*ICONS.keys(), extra=f'''
<linearGradient id="hdr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{TEAL}"/><stop offset="1" stop-color="{TEAL_DD}"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.4" fill="#ffffff" opacity=".07"/></pattern>'''))
    o.append(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

    # ---- header ----
    HH = 528
    o.append(f'<rect width="{W}" height="{HH}" fill="url(#hdr)"/>')
    o.append(f'<rect width="{W}" height="{HH}" fill="url(#dots)"/>')
    # decorative bidirectional wave
    o.append(f'<path d="M0 {HH - 6} C 300 {HH - 22}, 520 {HH + 8}, 820 {HH - 8} S 1340 {HH - 26}, 1600 {HH - 10}" '
             f'fill="none" stroke="{GOLD}" stroke-width="2" opacity=".4"/>')
    o.append(f'<path d="M1000 {HH - 120} C 1150 {HH - 170}, 1300 {HH - 60}, 1600 {HH - 130}" '
             f'fill="none" stroke="#ffffff" stroke-width="1.5" opacity=".10"/>')
    o.append(f'<image x="{W - M - 128}" y="58" width="128" height="148" href="data:image/png;base64,{CREST200}"/>')
    o.append(T(M, 92, "OCA OCPP 2.0.1 / 2.1 PLUGFEST & CONFERENCE AUSTRALIA", 19, 700, GOLD, "start", 'letter-spacing="2.2"'))
    o.append(T(M, 124, "21–23 October 2026  ·  Canberra", 19, 500, "#ffffff", "start", 'opacity=".85" letter-spacing=".5"'))
    o.append(T(M, 226, "From grid signal to", 78, 800, "#ffffff", "start", 'letter-spacing="-2"'))
    o.append(T(M, 312, "bidirectional charging profile", 78, 800, "#ffffff", "start", 'letter-spacing="-2"'))
    o.append(T(M, 390, "open, standard, end to end.", 60, 800, GOLD, "start", 'letter-spacing="-1.5"'))
    o.append(T(M, 444, "Home energy management that coordinates CSIP-AUS dynamic operating envelopes and OpenADR 3.1 price", 23, 400, CREAM))
    o.append(T(M, 476, "signals into OCPP 2.1 bidirectional charging profiles the charging station validates, responding quickly", 23, 400, CREAM))
    o.append(T(M, 508, "to price and network events, including 1-minute-notice Minimum System Load and Lack of Reserve events.", 23, 400, CREAM))

    # ---- section helper ----
    def section(y, num, title, sub=None):
        s = [f'<circle cx="{M + 20}" cy="{y - 8}" r="20" fill="{GOLD}"/>',
             T(M + 20, y - 1, num, 20, 800, INK, "middle"),
             T(M + 56, y, title, 32, 800, INK, "start", 'letter-spacing="-.6"')]
        if sub:
            s.append(T(W - M, y, sub, 16, 500, GREY, "end"))
        return "".join(s)

    # ---- 1. the chain ----
    y = 604
    o.append(section(y, "1", "Two signals in, one OCPP 2.1 profile out", "every component open source"))
    cy0 = y + 36
    tile_w = 206
    tile_h = 226
    c, gap = chain(M, cy0, CW, tile_w=tile_w, tile_h=tile_h)
    o.append(c)
    o.append(link_pills(M, cy0 + 240, CW, tile_w, gap, pw=200))
    hx = M + 2 * (tile_w + gap) + tile_w / 2
    o.append(price_lane(M, cy0 + 318, 326, 84, hx, cy0 + tile_h + 6))
    # payload callout
    by = cy0 + 418
    o.append(f'<rect x="{M}" y="{by}" width="{CW}" height="84" rx="16" fill="{CREAM}"/>')
    o.append(f'<rect x="{M}" y="{by}" width="8" height="84" rx="4" fill="{TEAL}"/>')
    o.append(TS(M + 32, by + 36, [("OCPP 2.1 SetChargingProfile", 800, TEAL_D),
                                  ("  ·  TxProfile  ·  CentralSetpoint  ·  setpoint / limit / dischargeLimit in W", 500, INK)], 19))
    o.append(T(M + 32, by + 64, "Prices travel with the power: absolutePriceSchedule on the profile · CostUpdated (California Pricing) · "
               "SetDefaultTariff. Not reliant on the OCPP 2.1 DER control block.", 16, 400, GREY))

    # ---- 2. proven ----
    y = by + 130
    o.append(section(y, "2", "Proven on 17 October 2026", "ANU BSGIP Cactus CSIP-AUS v1.2 test harness · EVerest DC V2G simulator"))
    sy0 = y + 34
    o.append(stat_cards(M, sy0, CW, 138))
    o.append(T(M, sy0 + 168, "Schedule-ahead: the bridge sends the next 600 s of CSIP-AUS controls as OCPP 2.1 profile periods, "
               "so each limit takes effect at its start time.", 16, 400, GREY))
    o.append(T(M, sy0 + 192, "In run 74865 every decrease applied 0.5–0.6 s early from the held profile, including 0 W.", 16, 400, GREY))

    # ---- 3. chart + 4. scenarios ----
    y = sy0 + 254
    o.append(section(y, "3", "One TxProfile, five setpoints"))
    o.append(T(M + 56, y + 30, "EVerest DC V2G simulator · ISO 15118-20 DC_BPT · ±25 kW rated · 60 s per step", 16, 500, GREY))
    chx, chw = M, 870
    chy = y + 52
    chh = 340
    o.append(f'<rect x="{chx}" y="{chy}" width="{chw}" height="{chh}" rx="18" fill="{CREAM}"/>')
    o.append(chart_legend(chx + 28, chy + 34, fs=0.92))
    o.append(chart(chx + 6, chy + 58, chw - 12, chh - 66, surface=CREAM))

    sx0 = M + chw + 32
    sw = W - M - sx0
    o.append(f'<circle cx="{sx0 + 20}" cy="{y - 8}" r="20" fill="{GOLD}"/>')
    o.append(T(sx0 + 20, y - 1, "4", 20, 800, INK, "middle"))
    o.append(T(sx0 + 56, y, "What the demo shows", 32, 800, INK, "start", 'letter-spacing="-.6"'))
    o.append(T(sx0 + 56, y + 30, "live, on the Plugfest floor", 16, 500, GREY))
    gcol, grow = 2, 3
    gg = 16
    cw2 = (sw - gg) / 2
    ch2 = (chh - 2 * gg) / 3
    for i, (ic, t1, t2) in enumerate(SCEN):
        cx = sx0 + (i % 2) * (cw2 + gg)
        cyy = chy + (i // 2) * (ch2 + gg)
        o.append(f'<rect x="{cx}" y="{cyy}" width="{cw2}" height="{ch2}" rx="16" fill="#ffffff" stroke="{RULE}" stroke-width="1.5"/>')
        o.append(f'<circle cx="{cx + 46}" cy="{cyy + ch2 / 2}" r="30" fill="{CREAM}"/>')
        o.append(icon(ic, cx + 46 - 23, cyy + ch2 / 2 - 23, 46))
        o.append(T(cx + 88, cyy + ch2 / 2 - 3, t1, 16, 700, INK))
        o.append(T(cx + 88, cyy + ch2 / 2 + 19, t2, 14, 400, GREY))

    # ---- 5. AS 5438 ----
    y = chy + chh + 64
    o.append(section(y, "5", "Draft AS 5438: three protocols an EEMS must support"))
    ay0 = y + 30
    ah = 142
    pw = 300
    for i, (name, sub, det, path, prim) in enumerate(AS):
        x = M + i * (pw + 16)
        o.append(f'<rect x="{x}" y="{ay0}" width="{pw}" height="{ah}" rx="16" fill="{TEAL if prim else "#ffffff"}" '
                 f'stroke="{TEAL if prim else RULE}" stroke-width="1.5"/>')
        o.append(T(x + 24, ay0 + 46, name, 26 if len(name) < 12 else 22, 800, "#ffffff" if prim else INK))
        o.append(T(x + 24, ay0 + 74, sub, 15, 500, CREAM if prim else GREY))
        o.append(T(x + 24, ay0 + 98, det, 14, 400, CREAM if prim else GREY))
        pc = GOLD if prim else CREAM
        tw = 116 if prim else 128
        o.append(f'<rect x="{x + 24}" y="{ay0 + 112}" width="{tw}" height="26" rx="13" fill="{pc}"/>')
        o.append(T(x + 24 + tw / 2, ay0 + 130, path, 13, 700, INK if prim else GREY, "middle"))
    tx = M + 3 * (pw + 16) + 8
    tw2 = W - M - tx
    o.append(f'<rect x="{tx}" y="{ay0}" width="{tw2}" height="{ah}" rx="16" fill="{CREAM}"/>')
    o.append(T(tx + 24, ay0 + 34, "AS 5438 function-map timing targets", 15, 700, TEAL_D))
    colw = (tw2 - 48) / 3
    for i, (v, l) in enumerate(TIMING):
        xx = tx + 24 + i * colw
        o.append(T(xx, ay0 + 88, v, 36, 800, INK, "start", 'letter-spacing="-.8"'))
        o.append(T(xx, ay0 + 118, l, 14, 500, GREY))

    # ---- footer ----
    fy = H - 136
    o.append(f'<rect x="0" y="{fy}" width="{W}" height="136" fill="{TEAL_DD}"/>')
    o.append(f'<rect x="0" y="{fy}" width="{W}" height="5" fill="{GOLD}"/>')
    o.append(f'<image x="{M}" y="{fy + 22}" width="80" height="92" href="data:image/png;base64,{CREST120}"/>')
    o.append(T(M + 104, fy + 54, "Mark Purcell AM", 26, 800, "#ffffff"))
    o.append(T(M + 104, fy + 82, "purcell.id.au Pty Ltd · Sunshine Coast, QLD", 17, 400, CREAM))
    o.append(T(M + 104, fy + 108, "Also at the Plugfest as a CSMS under test: CitrineOS on Home Assistant Green, Security Profile 1", 15, 400, "#bcd6d2"))
    o.append(T(W - M, fy + 54, "github.com/purcell-lab/ocpp-plugfest", 24, 800, GOLD, "end"))
    o.append(T(W - M, fy + 82, "OCA OCPP Plugfest & Conference · Canberra · 21–23 Oct 2026", 17, 400, CREAM, "end"))
    o.append("</svg>")
    return "".join(o)


# ============================================================
#  README ASSETS
# ============================================================
def panel(w, h, fill=CREAM, r=24):
    return f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="{r}" fill="{fill}" stroke="{RULE}" stroke-width="2"/>'


def hero():
    W, H = 1280, 476
    o = [svg_open(W, H, "OCPP Plugfest Australia 2026: from grid signal to bidirectional charging profile",
                  "Open, standard, end to end: CSIP-AUS dynamic operating envelopes and OpenADR 3.1 price signals "
                  "converge on the Home Assistant EEMS, which sends OCPP 2.1 bidirectional charging profiles to the charging station.")]
    o.append(defs(*[c[0] for c in CHAIN], PRICE_SRC[0], extra=f'''
<linearGradient id="hdr" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{TEAL}"/><stop offset="1" stop-color="{TEAL_DD}"/></linearGradient>
<pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.3" fill="#ffffff" opacity=".07"/></pattern>
<clipPath id="pc"><rect x="0" y="0" width="{W}" height="{H}" rx="24"/></clipPath>'''))
    o.append(f'<g clip-path="url(#pc)"><rect width="{W}" height="{H}" fill="url(#hdr)"/><rect width="{W}" height="{H}" fill="url(#dots)"/>')
    o.append(f'<path d="M0 {H - 8} C 260 {H - 26}, 460 {H + 6}, 700 {H - 10} S 1100 {H - 28}, 1280 {H - 12}" fill="none" stroke="{GOLD}" stroke-width="2" opacity=".35"/></g>')
    o.append(f'<image x="{W - 56 - 92}" y="40" width="92" height="106" href="data:image/png;base64,{CREST200}"/>')
    o.append(T(56, 70, "OCA OCPP 2.0.1 / 2.1 PLUGFEST · CANBERRA · 21–23 OCT 2026", 16, 700, GOLD, "start", 'letter-spacing="1.8"'))
    o.append(T(56, 138, "From grid signal to", 52, 800, "#ffffff", "start", 'letter-spacing="-1.4"'))
    o.append(T(56, 196, "bidirectional charging profile", 52, 800, "#ffffff", "start", 'letter-spacing="-1.4"'))
    o.append(T(56, 246, "open, standard, end to end.", 38, 800, GOLD, "start", 'letter-spacing="-1"'))
    # mini chain: two input lanes (network, price) merge into Home Assistant, then one lane to the EV
    R = 28
    y1, y2 = 304, 398            # network lane, price lane
    ym = (y1 + y2) / 2           # main lane
    n = 6
    x0, x1 = 56, W - 56
    step = (x1 - x0) / (n - 1)
    X = [x0 + i * step for i in range(n)]
    st = f'stroke="{GOLD}" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" opacity=".9"'

    def head(xb, yb):
        return f'<path d="M{xb - 8} {yb - 5} L{xb} {yb} L{xb + 0} {yb} L{xb - 8} {yb + 5}" {st}/>'

    def lbl(x, y, s):
        return T(x, y, s, 13, 700, GOLD_L, "middle", 'letter-spacing=".3"')

    # network lane: CSIP-AUS -> ODE
    xa, xb = X[0] + R + 6, X[1] - R - 6
    o.append(f'<path d="M{xa} {y1} H{xb}" {st}/>' + head(xb, y1) + lbl((xa + xb) / 2, y1 - 10, "SEP2"))
    # ODE -> Home Assistant (curves down into the main lane)
    ha_in = X[2] - R - 6
    xa = X[1] + R + 6
    xc = ha_in - 64
    o.append(f'<path d="M{xa} {y1} H{xc} C{xc + 34} {y1} {xc + 30} {ym - 9} {ha_in} {ym - 9}" {st}/>' + head(ha_in, ym - 9)
             + lbl((xa + xc) / 2, y1 - 10, "MQTT"))
    # price lane: OpenADR VTN -> Home Assistant (curves up into the main lane)
    xa = X[0] + R + 6
    o.append(f'<path d="M{xa} {y2} H{xc} C{xc + 34} {y2} {xc + 30} {ym + 9} {ha_in} {ym + 9}" {st}/>' + head(ha_in, ym + 9)
             + lbl((xa + xc) / 2, y2 - 10, "OpenADR 3.1"))
    # main lane: Home Assistant -> CitrineOS -> EVerest -> EV
    protos = ["REST", "OCPP 2.1", "ISO 15118-20"]
    for i in range(2, n - 1):
        xa, xb = X[i] + R + 6, X[i + 1] - R - 6
        o.append(f'<path d="M{xa} {ym} H{xb}" {st}/>' + head(xb, ym) + lbl((xa + xb) / 2, ym - 10, protos[i - 2]))
    labels = ["CSIP-AUS server", "ODE", "Home Assistant", "CitrineOS", "EVerest → Plugfest stations", "EV"]
    nodes = [(X[0], y1, CHAIN[0][0], labels[0], "start"), (X[1], y1, CHAIN[1][0], labels[1], "middle"),
             (X[0], y2, PRICE_SRC[0], "OpenADR 3.1 VTN", "start")]
    nodes += [(X[i], ym, CHAIN[i][0], labels[i], "end" if i == n - 1 else "middle") for i in range(2, n)]
    for cx, cy, ic, lab, anchor in nodes:
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{CREAM}"/>')
        o.append(icon(ic, cx - 20, cy - 20, 40))
        ax = cx - R if anchor == "start" else (cx + R if anchor == "end" else cx)
        o.append(T(ax, cy + R + 22, lab, 15, 600, "#ffffff", anchor))
    o.append("</svg>")
    return "".join(o)


def flow():
    W, H = 1280, 448
    o = [svg_open(W, H, "End-to-end chain with protocol labels",
                  "Two inputs converge on the Home Assistant EEMS. Network: the network operator's CSIP-AUS server (Cactus) via SEP2/CSIP-AUS "
                  "to Open Dynamic Export, via MQTT to Home Assistant. Price: an OpenADR 3.1 VTN via OpenADR 3.1 PRICE and EXPORT_PRICE "
                  "events to Home Assistant (OpenADR VEN). Then via REST to CitrineOS CSMS, via OCPP 2.1 SetChargingProfile to EVerest, "
                  "then the Plugfest charging stations, via ISO 15118-20 DC_BPT to the EV.")]
    o.append(defs(*[c[0] for c in CHAIN], PRICE_SRC[0]))
    o.append(panel(W, H))
    M = 36
    tile_w = 176
    tile_h = 224
    c, gap = chain(M, 28, W - 2 * M, tile_w=tile_w, tile_h=tile_h, f1=17, f2=13)
    o.append(c)
    o.append(link_pills(M, 266, W - 2 * M, tile_w, gap, h=52, size1=15, size2=12.5, pw=170))
    hx = M + 2 * (tile_w + gap) + tile_w / 2
    o.append(price_lane(M, 336, 266, 82, hx, 28 + tile_h + 6, f1=17, f2=13, r=30, icon_sz=46,
                        pw=178, ph=52, ps1=15, ps2=12.5))
    o.append("</svg>")
    return "".join(o)


def stats():
    W, H = 1280, 210
    o = [svg_open(W, H, "Proven on 17 October 2026",
                  "LOA-11 16/16 on AC and DC V2G chargers; plus/minus 20 kW tracked exactly; 25 kW bidirectional; 600 s schedule-ahead; 100% open source.")]
    o.append(panel(W, H))
    o.append(stat_cards(24, 24, W - 48, H - 48, sizes=(40, 15, 12.5), bg="#ffffff"))
    o.append("</svg>")
    return "".join(o)


def v2g():
    W, H = 1000, 460
    o = [svg_open(W, H, "OCPP 2.1 CentralSetpoint TxProfile: setpoint vs charger meter",
                  "One TxProfile with steps +20, -20, +6, -5 and 0 kW, 60 s each. The charger meter matched every step, "
                  "each within about one 5 s meter sample of the step boundary.")]
    o.append(panel(W, H))
    o.append(T(32, 48, "One OCPP 2.1 TxProfile, five setpoints: the meter tracked every step", 22, 800, INK, "start", 'letter-spacing="-.4"'))
    o.append(T(32, 74, "EVerest DC V2G simulator · ISO 15118-20 DC_BPT · ±25 kW rated · 60 s per step · 17 Oct 2026", 14, 500, GREY))
    o.append(chart_legend(34, 104, fs=0.92))
    o.append(chart(10, 122, W - 24, H - 132, surface=CREAM, fs=0.95))
    o.append("</svg>")
    return "".join(o)


def scenarios():
    W, H = 1280, 300
    o = [svg_open(W, H, "What the demo shows",
                  "Export-limit clip during V2G discharge, import-limit clip during charging, load-limit clip, "
                  "1-minute MSL and LOR events, local network congestion, OpenADR 3.1 price events.")]
    o.append(defs(*[s[0] for s in SCEN]))
    o.append(panel(W, H))
    o.append(T(32, 50, "What the demo shows", 24, 800, INK, "start", 'letter-spacing="-.4"'))
    o.append(T(W - 32, 50, "CSIP-AUS envelopes + OpenADR prices → OCPP 2.1 profiles, live", 15, 500, GREY, "end"))
    n = 6
    gap = 16
    cw = (W - 64 - gap * (n - 1)) / n
    for i, (ic, t1, t2) in enumerate(SCEN):
        x = 32 + i * (cw + gap)
        y = 76
        o.append(f'<rect x="{x}" y="{y}" width="{cw}" height="196" rx="16" fill="#ffffff" stroke="{RULE}" stroke-width="1.5"/>')
        o.append(f'<circle cx="{x + cw / 2}" cy="{y + 64}" r="40" fill="{CREAM}"/>')
        o.append(icon(ic, x + cw / 2 - 30, y + 34, 60))
        o.append(T(x + cw / 2, y + 140, t1, 16, 700, INK, "middle"))
        o.append(T(x + cw / 2, y + 164, t2, 14, 400, GREY, "middle"))
    o.append("</svg>")
    return "".join(o)


def as5438():
    W, H = 1280, 230
    o = [svg_open(W, H, "Draft AS 5438: three protocols and timing targets",
                  "SEP2 via CSIP-AUS and OCPP 2.1 are the primary paths; SunSpec Modbus 1.2 is secondary. "
                  "Timing targets: 5 s read/write, 30 s active-power limit, 15 s communication-loss fail-safe.")]
    o.append(defs("check"))
    o.append(panel(W, H))
    o.append(T(32, 48, "Draft AS 5438: three protocols an EEMS must support", 22, 800, INK, "start", 'letter-spacing="-.4"'))
    y0 = 70
    ah = 132
    pw = 240
    for i, (name, sub, det, path, prim) in enumerate(AS):
        x = 32 + i * (pw + 14)
        o.append(f'<rect x="{x}" y="{y0}" width="{pw}" height="{ah}" rx="14" fill="{TEAL if prim else "#ffffff"}" '
                 f'stroke="{TEAL if prim else RULE}" stroke-width="1.5"/>')
        o.append(T(x + 20, y0 + 40, name, 24 if len(name) < 12 else 19, 800, "#ffffff" if prim else INK))
        o.append(T(x + 20, y0 + 66, sub, 14, 500, CREAM if prim else GREY))
        o.append(T(x + 20, y0 + 88, det, 13, 400, CREAM if prim else GREY))
        pc = GOLD if prim else CREAM
        tw = 104 if prim else 116
        o.append(f'<rect x="{x + 20}" y="{y0 + 100}" width="{tw}" height="22" rx="11" fill="{pc}"/>')
        o.append(T(x + 20 + tw / 2, y0 + 115.5, path, 12, 700, INK if prim else GREY, "middle"))
    tx = 32 + 3 * (pw + 14) + 6
    tw2 = W - 32 - tx
    o.append(f'<rect x="{tx}" y="{y0}" width="{tw2}" height="{ah}" rx="14" fill="#ffffff" stroke="{RULE}" stroke-width="1.5"/>')
    o.append(T(tx + 22, y0 + 32, "AS 5438 function-map timing targets", 14, 700, TEAL_D))
    colw = (tw2 - 44) / 3
    for i, (v, l) in enumerate(TIMING):
        xx = tx + 22 + i * colw
        o.append(T(xx, y0 + 84, v, 32, 800, INK, "start", 'letter-spacing="-.8"'))
        o.append(T(xx, y0 + 112, l, 13, 500, GREY))
    o.append("</svg>")
    return "".join(o)


if __name__ == "__main__":
    out = {
        "infographic/plugfest-infographic.svg": infographic(),
        "assets/hero.svg": hero(),
        "assets/flow.svg": flow(),
        "assets/stats.svg": stats(),
        "assets/v2g-txprofile.svg": v2g(),
        "assets/scenarios.svg": scenarios(),
        "assets/as5438.svg": as5438(),
    }
    for p, s in out.items():
        with open(os.path.join(ROOT, p), "w") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n' + s + "\n")
        print(p, len(s))
